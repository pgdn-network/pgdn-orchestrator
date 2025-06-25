"""
Main orchestration agent implementation
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

from .models import (
    OrchestrationDecision, 
    Node, 
    Organisation, 
    ScanPolicy,
    ScanLevel,
    NextAction
)
from .exceptions import AIProviderError, InvalidConfigurationError, PermissionDeniedError
from .prompts import PromptGenerator

logger = logging.getLogger(__name__)

class OrchestrationAgent:
    """
    AI-powered orchestration agent for DePIN scan decisions
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o",
        anthropic_model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.2,
        enable_fallback: bool = True
    ):
        """
        Initialize the orchestration agent
        
        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            anthropic_api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            openai_model: OpenAI model to use
            anthropic_model: Anthropic model to use
            temperature: AI temperature setting
            enable_fallback: Enable fallback between providers
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.openai_model = openai_model
        self.anthropic_model = anthropic_model
        self.temperature = float(os.getenv("ORCHESTRATION_TEMPERATURE", temperature))
        self.enable_fallback = enable_fallback
        
        self.prompt_generator = PromptGenerator()
        
        # Initialize clients
        self._init_clients()
        
    def _init_clients(self):
        """Initialize AI provider clients"""
        self.openai_client = None
        self.anthropic_client = None
        
        if self.anthropic_api_key and anthropic:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("Initialized Anthropic client")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        if self.openai_api_key and openai:
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        if not self.anthropic_client and not self.openai_client:
            raise InvalidConfigurationError(
                "No AI provider available. Please provide OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
    
    def decide(
        self, 
        node: Dict[str, Any], 
        organisation: Dict[str, Any], 
        scan_policy: Dict[str, Any]
    ) -> OrchestrationDecision:
        """
        Make an orchestration decision for a node
        
        Args:
            node: Node metadata dictionary
            organisation: Organisation context dictionary  
            scan_policy: Scan policy configuration dictionary
            
        Returns:
            OrchestrationDecision with next action and reasoning
        """
        # Convert dicts to Pydantic models for validation
        node_obj = Node(**node) if isinstance(node, dict) else node
        org_obj = Organisation(**organisation) if isinstance(organisation, dict) else organisation
        policy_obj = ScanPolicy(**scan_policy) if isinstance(scan_policy, dict) else scan_policy
        
        # Apply business logic checks first
        self._validate_permissions(node_obj, org_obj, policy_obj)
        
        # Generate prompt
        prompt = self.prompt_generator.generate_orchestration_prompt(
            node_obj, org_obj, policy_obj
        )
        
        # Get AI decision
        decision_data = self._get_ai_decision(prompt)
        
        # Validate and return decision
        decision = OrchestrationDecision(**decision_data)
        self._validate_decision(decision, node_obj, org_obj, policy_obj)
        
        logger.info(f"Orchestration decision for node {node_obj.id}: {decision.next_action}")
        return decision
    
    def _validate_permissions(self, node: Node, org: Organisation, policy: ScanPolicy):
        """Validate permissions before making decision"""
        
        # Check if host is blacklisted
        if node.host in org.blacklisted_hosts:
            raise PermissionDeniedError(f"Host {node.host} is blacklisted for organisation {org.id}")
        
        # Check protocol whitelist if configured
        if org.whitelisted_protocols and node.protocol:
            if node.protocol not in org.whitelisted_protocols:
                raise PermissionDeniedError(
                    f"Protocol {node.protocol} not whitelisted for organisation {org.id}"
                )
    
    def _validate_decision(self, decision: OrchestrationDecision, node: Node, org: Organisation, policy: ScanPolicy):
        """Validate the AI decision against business rules"""
        
        # Check ferocious scan permissions
        if decision.scan_level == "ferocious" and not org.ferocious_enabled:
            logger.warning(f"AI recommended ferocious scan but org {org.id} lacks permission, downgrading to medium")
            decision.scan_level = "medium"
            decision.next_action = "scan_medium"
        
        # Check scan cooldown
        if node.last_scan_time and decision.next_action.startswith("scan_"):
            cooldown_delta = timedelta(hours=policy.scan_cooldown_hours)
            if datetime.utcnow() - node.last_scan_time < cooldown_delta:
                logger.info(f"Node {node.id} in cooldown period, skipping scan")
                decision.next_action = "skip"
                decision.scan_level = None
        
        # Enforce maximum escalation policy
        escalation_order = {"light": 1, "medium": 2, "ferocious": 3}
        max_level = escalation_order.get(policy.max_escalation, 2)
        
        if decision.scan_level and escalation_order.get(decision.scan_level, 1) > max_level:
            # Downgrade to maximum allowed level
            for level, order in escalation_order.items():
                if order == max_level:
                    decision.scan_level = level
                    decision.next_action = f"scan_{level}"
                    break
    
    def _get_ai_decision(self, prompt: str) -> Dict[str, Any]:
        """Get decision from AI provider with fallback"""
        
        # Try Anthropic first if available
        if self.anthropic_client:
            try:
                return self._call_anthropic(prompt)
            except Exception as e:
                logger.warning(f"Anthropic call failed: {e}")
                if not self.enable_fallback or not self.openai_client:
                    raise AIProviderError(f"Anthropic call failed: {e}")
        
        # Fall back to OpenAI
        if self.openai_client:
            try:
                return self._call_openai(prompt)
            except Exception as e:
                logger.error(f"OpenAI call failed: {e}")
                raise AIProviderError(f"OpenAI call failed: {e}")
        
        raise AIProviderError("No AI provider available")
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API"""
        logger.debug("Calling Anthropic API")
        
        response = self.anthropic_client.messages.create(
            model=self.anthropic_model,
            max_tokens=1024,
            temperature=self.temperature,
            system="You are an infrastructure orchestration agent. Output must be valid JSON that matches the required schema exactly.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Clean up potential markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        logger.debug("Calling OpenAI API")
        
        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an infrastructure orchestration agent. Output must be valid JSON that matches the required schema exactly."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        text = response.choices[0].message.content.strip()
        return json.loads(text)
