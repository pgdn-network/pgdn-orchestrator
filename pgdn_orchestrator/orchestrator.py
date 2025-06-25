from pgdn.scanning.scan_orchestrator import ScanOrchestrator
from pgdn.core.config import Config

def run_scan(target, org_id, scan_level=1):
    """
    Run a scan using the external pgdn library's ScanOrchestrator.
    Args:
        target (str): The target host/IP to scan.
        org_id (str): The organization ID.
        scan_level (int): Scan level (1, 2, or 3).
    Returns:
        dict: Scan results from the orchestrator.
    """
    config = Config()
    orchestrator = ScanOrchestrator(config)
    return orchestrator.scan(target, org_id=org_id, scan_level=scan_level) 