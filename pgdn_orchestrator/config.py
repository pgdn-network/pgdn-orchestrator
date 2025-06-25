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
