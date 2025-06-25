"""
Prompt generation for AI orchestration decisions
"""

from .models import Node, Organisation, ScanPolicy

class PromptGenerator:
    """Generates prompts for AI orchestration decisions"""
    
    def generate_orchestration_prompt(
        self, 
        node: Node, 
        organisation: Organisation, 
        scan_policy: ScanPolicy
    ) -> str:
        """Generate the main orchestration prompt"""
        
        return f"""You are a DePIN orchestration agent responsible for deciding the next scanning action on a node.

Each node can be scanned at one of three levels:
- light: basic recon and port scanning
- medium: service analysis, vulnerability detection, and trust scoring  
- ferocious: deep, aggressive scan with comprehensive security assessment (requires permission)

Instructions:
- Evaluate the node's current state (new, failing, known, open ports, protocol, scan history, etc).
- Check the designated protocol. If unknown and the node is new, recommend discovery first.
- Verify the organisation's permissions for running ferocious scans.
- Consider scan cooldown periods and escalation policies.
- Do not escalate scanning without protocol classification or required permissions.
- Recommend only the next immediate action based on current state.
- Suggest logical follow-up actions based on likely outcomes.

Available actions:
- run_discovery: Identify the node's protocol and services
- scan_light: Basic reconnaissance scan
- scan_medium: Standard security assessment
- scan_ferocious: Comprehensive security analysis (requires org permission)
- manual_review: Flag for human investigation
- skip: Skip scanning (e.g., due to cooldown or policy)

Return your result in JSON using the following schema:

```json
{{
  "next_action": "run_discovery",
  "scan_level": "light",
  "reasoning": "Detailed explanation of decision logic",
  "expected_follow_up": [
    {{
      "condition": "discovery succeeds and identifies validator protocol",
      "action": "scan_medium"
    }},
    {{
      "condition": "discovery fails after 3 attempts",
      "action": "manual_review"
    }}
  ],
  "confidence": 0.85
}}
```

Node metadata:
- ID: {node.id}
- Host: {node.host}
- Protocol: {node.protocol or "Unknown"}
- Status: {node.status}
- Last scan: {node.last_scan_time or "Never"}
- Last scan level: {node.last_scan_level or "None"}
- Discovery attempts: {node.discovery_attempts}
- Scan failures: {node.scan_failures}
- Open ports: {node.open_ports}
- Services: {node.services}
- Trust score: {node.trust_score or "Not calculated"}
- Scan history count: {len(node.scan_history)}

Organisation context:
- ID: {organisation.id}
- Name: {organisation.name or "Unknown"}
- Ferocious scans enabled: {organisation.ferocious_enabled}
- Max concurrent scans: {organisation.max_concurrent_scans}
- Daily scan budget: {organisation.scan_budget_daily or "Unlimited"}
- Whitelisted protocols: {organisation.whitelisted_protocols or "All"}
- Blacklisted hosts: {len(organisation.blacklisted_hosts)} hosts

Global scan policy:
- Max escalation level: {scan_policy.max_escalation}
- Require discovery: {scan_policy.require_discovery}
- Max discovery attempts: {scan_policy.max_discovery_attempts}
- Scan cooldown hours: {scan_policy.scan_cooldown_hours}
- Auto escalation enabled: {scan_policy.auto_escalation_enabled}
- Trust thresholds: medium={scan_policy.trust_score_threshold_medium}, ferocious={scan_policy.trust_score_threshold_ferocious}

Decision Guidelines:
1. New nodes with unknown protocol should start with discovery
2. Nodes with low trust scores may warrant escalated scanning (if permitted)
3. Failed discovery attempts should trigger manual review after max attempts
4. Respect cooldown periods between scans
5. Consider escalation based on previous scan results and trust scores
6. Always check organisational permissions before recommending ferocious scans
"""
