"""
Data models for orchestration decisions and input structures
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

ScanLevel = Literal["light", "medium", "ferocious"]
NextAction = Literal["run_discovery", "scan_light", "scan_medium", "scan_ferocious", "manual_review", "skip"]

class FollowUpAction(BaseModel):
    """Expected follow-up action based on conditions"""
    condition: str = Field(..., description="Condition that triggers this action")
    action: str = Field(..., description="Action to take when condition is met")

class OrchestrationDecision(BaseModel):
    """AI orchestration decision output"""
    next_action: NextAction = Field(..., description="Immediate next action to take")
    scan_level: Optional[ScanLevel] = Field(None, description="Scan level if action is a scan")
    reasoning: str = Field(..., description="Explanation for the decision")
    expected_follow_up: List[FollowUpAction] = Field(
        default_factory=list,
        description="Expected follow-up actions based on outcomes"
    )
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Node(BaseModel):
    """Node metadata for orchestration decisions"""
    id: str = Field(..., description="Unique node identifier")
    host: str = Field(..., description="Node hostname or IP address")
    protocol: Optional[str] = Field(None, description="Identified protocol (sui, filecoin, etc.)")
    last_scan_time: Optional[datetime] = Field(None, description="Timestamp of last scan")
    last_scan_level: Optional[ScanLevel] = Field(None, description="Level of last scan performed")
    scan_history: List[Dict[str, Any]] = Field(default_factory=list, description="Previous scan results")
    open_ports: List[int] = Field(default_factory=list, description="Known open ports")
    services: Dict[str, str] = Field(default_factory=dict, description="Identified services")
    trust_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Current trust score")
    discovery_attempts: int = Field(default=0, description="Number of discovery attempts")
    scan_failures: int = Field(default=0, description="Number of consecutive scan failures")
    status: Literal["new", "active", "failing", "offline", "unknown"] = Field(default="new")

class Organisation(BaseModel):
    """Organisation context and permissions"""
    id: str = Field(..., description="Organisation identifier")
    name: Optional[str] = Field(None, description="Organisation name")
    ferocious_enabled: bool = Field(default=False, description="Permission for ferocious scans")
    max_concurrent_scans: int = Field(default=10, description="Maximum concurrent scans allowed")
    scan_budget_daily: Optional[int] = Field(None, description="Daily scan budget limit")
    whitelisted_protocols: List[str] = Field(default_factory=list, description="Protocols org is authorized to scan")
    blacklisted_hosts: List[str] = Field(default_factory=list, description="Hosts to never scan")
    scan_preferences: Dict[str, Any] = Field(default_factory=dict, description="Custom scan preferences")

class ScanPolicy(BaseModel):
    """Global scan policy configuration"""
    max_escalation: ScanLevel = Field(default="medium", description="Maximum allowed scan level")
    require_discovery: bool = Field(default=True, description="Require protocol discovery before scanning")
    max_discovery_attempts: int = Field(default=3, description="Maximum discovery attempts before manual review")
    scan_cooldown_hours: int = Field(default=24, description="Hours between scans of same node")
    auto_escalation_enabled: bool = Field(default=True, description="Allow automatic scan escalation")
    trust_score_threshold_medium: float = Field(default=70.0, description="Trust score threshold for medium scans")
    trust_score_threshold_ferocious: float = Field(default=50.0, description="Trust score threshold for ferocious scans")
