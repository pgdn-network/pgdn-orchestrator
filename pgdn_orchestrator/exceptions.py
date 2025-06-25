"""
Custom exceptions for orchestration
"""

class OrchestrationError(Exception):
    """Base exception for orchestration errors"""
    pass

class AIProviderError(OrchestrationError):
    """Error communicating with AI provider"""
    pass

class InvalidConfigurationError(OrchestrationError):
    """Invalid configuration error"""
    pass

class PermissionDeniedError(OrchestrationError):
    """Permission denied for requested action"""
    pass
