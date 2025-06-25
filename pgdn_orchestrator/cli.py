# pgdn_orchestrator/cli.py
"""
Command-line interface for pgdn-orchestrator
"""

import argparse
import json
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .agent import OrchestrationAgent
from .models import Node, Organisation, ScanPolicy
from .exceptions import OrchestrationError
from pgdn_orchestrator.orchestrator import run_scan

logger = logging.getLogger(__name__)

def setup_logging(debug: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_config_file(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file"""
    if not config_path:
        return {}
    
    config_file = Path(config_path)
    if not config_file.exists():
        logger.warning(f"Config file {config_path} not found")
        return {}
    
    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        return {}

def create_default_node(target: str, node_id: Optional[str] = None) -> Dict[str, Any]:
    """Create default node configuration"""
    import uuid
    return {
        "id": node_id or str(uuid.uuid4()),
        "host": target,
        "protocol": None,
        "status": "new",
        "discovery_attempts": 0,
        "scan_failures": 0,
        "open_ports": [],
        "services": {},
        "scan_history": []
    }

def create_default_organisation(org_id: str) -> Dict[str, Any]:
    """Create default organisation configuration"""
    return {
        "id": org_id,
        "name": f"Organisation {org_id}",
        "ferocious_enabled": False,
        "max_concurrent_scans": 10,
        "whitelisted_protocols": [],
        "blacklisted_hosts": [],
        "scan_preferences": {}
    }

def create_default_scan_policy() -> Dict[str, Any]:
    """Create default scan policy"""
    return {
        "max_escalation": "medium",
        "require_discovery": True,
        "max_discovery_attempts": 3,
        "scan_cooldown_hours": 24,
        "auto_escalation_enabled": True,
        "trust_score_threshold_medium": 70.0,
        "trust_score_threshold_ferocious": 50.0
    }

def main():
    parser = argparse.ArgumentParser(description="Run a scan using the PGDN orchestrator.")
    parser.add_argument("--target", required=True, help="Target host/IP to scan")
    parser.add_argument("--org-id", required=True, help="Organization ID")
    parser.add_argument("--scan-level", type=int, default=1, help="Scan level (1, 2, or 3)")
    args = parser.parse_args()

    result = run_scan(args.target, args.org_id, args.scan_level)
    print(result)

if __name__ == "__main__":
    main()

# pgdn_orchestrator/integration.py
"""
Integration helpers for pgdn command line tool
"""

import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .agent import OrchestrationAgent
from .models import OrchestrationDecision

logger = logging.getLogger(__name__)

class PgdnIntegration:
    """Integration layer for pgdn command line tool"""
    
    def __init__(self, pgdn_binary: str = "pgdn"):
        """
        Initialize integration
        
        Args:
            pgdn_binary: Path to pgdn binary (default: "pgdn")
        """
        self.pgdn_binary = pgdn_binary
        self.agent = OrchestrationAgent()
    
    def orchestrate_and_execute(
        self,
        target: str,
        org_id: str,
        node_data: Optional[Dict[str, Any]] = None,
        org_data: Optional[Dict[str, Any]] = None,
        policy_data: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        additional_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Make orchestration decision and optionally execute pgdn command
        
        Args:
            target: Target host/IP
            org_id: Organisation ID
            node_data: Node metadata (will create defaults if None)
            org_data: Organisation data (will create defaults if None)  
            policy_data: Scan policy (will create defaults if None)
            dry_run: If True, only return decision without executing
            additional_args: Additional arguments to pass to pgdn
            
        Returns:
            Dict containing decision and execution results
        """
        from .cli import create_default_node, create_default_organisation, create_default_scan_policy
        
        # Create defaults if not provided
        if node_data is None:
            node_data = create_default_node(target)
        if org_data is None:
            org_data = create_default_organisation(org_id)
        if policy_data is None:
            policy_data = create_default_scan_policy()
        
        # Make orchestration decision
        decision = self.agent.decide(node_data, org_data, policy_data)
        
        result = {
            "decision": decision.model_dump(),
            "target": target,
            "org_id": org_id,
            "executed": False,
            "pgdn_result": None,
            "pgdn_command": None
        }
        
        if dry_run:
            return result
        
        # Build and execute pgdn command
        pgdn_cmd = self._build_pgdn_command(decision, target, org_id, additional_args)
        result["pgdn_command"] = " ".join(pgdn_cmd)
        
        if decision.next_action != "skip":
            try:
                pgdn_result = self._execute_pgdn(pgdn_cmd)
                result["pgdn_result"] = pgdn_result
                result["executed"] = True
                logger.info(f"Successfully executed: {result['pgdn_command']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"pgdn command failed: {e}")
                result["pgdn_result"] = {"error": str(e), "returncode": e.returncode}
        else:
            logger.info(f"Skipping execution due to decision: {decision.next_action}")
        
        return result
    
    def _build_pgdn_command(
        self,
        decision: OrchestrationDecision,
        target: str,
        org_id: str,
        additional_args: Optional[List[str]] = None
    ) -> List[str]:
        """Build pgdn command based on orchestration decision"""
        
        cmd = [self.pgdn_binary]
        
        # Map decision to pgdn stage and arguments
        if decision.next_action == "run_discovery":
            cmd.extend(["--stage", "discovery", "--target", target])
        elif decision.next_action.startswith("scan_"):
            cmd.extend(["--stage", "scan", "--target", target])
            if decision.scan_level:
                cmd.extend(["--scan-level", decision.scan_level])
        elif decision.next_action == "manual_review":
            # For manual review, we might want to log or create a ticket
            # For now, just do a basic scan for information gathering
            cmd.extend(["--stage", "scan", "--target", target, "--scan-level", "light"])
        else:
            # Default fallback
            cmd.extend(["--stage", "scan", "--target", target])
        
        # Add organisation ID
        cmd.extend(["--org-id", org_id])
        
        # Add additional arguments if provided
        if additional_args:
            cmd.extend(additional_args)
        
        return cmd
    
    def _execute_pgdn(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute pgdn command and return results"""
        
        logger.debug(f"Executing command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": True
            }
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise subprocess.CalledProcessError(124, cmd, "Command timed out")
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with return code {e.returncode}: {' '.join(cmd)}")
            return {
                "returncode": e.returncode,
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
                "success": False,
                "error": str(e)
            }

# pgdn_orchestrator/config.py
"""
Configuration management for pgdn-orchestrator
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages configuration for orchestration"""
    
    DEFAULT_CONFIG = {
        "ai_provider": {
            "prefer_anthropic": True,
            "temperature": 0.2,
            "openai_model": "gpt-4o",
            "anthropic_model": "claude-3-5-sonnet-20241022"
        },
        "scan_policy": {
            "max_escalation": "medium",
            "require_discovery": True,
            "max_discovery_attempts": 3,
            "scan_cooldown_hours": 24,
            "auto_escalation_enabled": True,
            "trust_score_threshold_medium": 70.0,
            "trust_score_threshold_ferocious": 50.0
        },
        "pgdn_integration": {
            "binary_path": "pgdn",
            "default_timeout": 300,
            "retry_attempts": 2
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment"""
        config = self.DEFAULT_CONFIG.copy()
        
        # Load from file if provided
        if self.config_path:
            file_path = Path(self.config_path)
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        file_config = json.load(f)
                    self._deep_update(config, file_config)
                except Exception as e:
                    print(f"Warning: Failed to load config file {self.config_path}: {e}")
        
        # Override with environment variables
        self._load_env_overrides(config)
        
        return config
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]):
        """Deep update dictionary"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _load_env_overrides(self, config: Dict[str, Any]):
        """Load configuration overrides from environment variables"""
        
        # AI provider settings
        if os.getenv("ORCHESTRATION_TEMPERATURE"):
            config["ai_provider"]["temperature"] = float(os.getenv("ORCHESTRATION_TEMPERATURE"))
        if os.getenv("OPENAI_MODEL"):
            config["ai_provider"]["openai_model"] = os.getenv("OPENAI_MODEL")
        if os.getenv("ANTHROPIC_MODEL"):
            config["ai_provider"]["anthropic_model"] = os.getenv("ANTHROPIC_MODEL")
        
        # Scan policy settings
        if os.getenv("ORCHESTRATION_MAX_ESCALATION"):
            config["scan_policy"]["max_escalation"] = os.getenv("ORCHESTRATION_MAX_ESCALATION")
        if os.getenv("ORCHESTRATION_SCAN_COOLDOWN"):
            config["scan_policy"]["scan_cooldown_hours"] = int(os.getenv("ORCHESTRATION_SCAN_COOLDOWN"))
        
        # pgdn integration
        if os.getenv("PGDN_BINARY_PATH"):
            config["pgdn_integration"]["binary_path"] = os.getenv("PGDN_BINARY_PATH")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path to config value (e.g., "ai_provider.temperature")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def save(self, output_path: Optional[str] = None):
        """
        Save current configuration to file
        
        Args:
            output_path: Path to save config (defaults to original config_path)
        """
        save_path = output_path or self.config_path
        if not save_path:
            raise ValueError("No output path specified")
        
        with open(save_path, 'w') as f:
            json.dump(self.config, f, indent=2)
