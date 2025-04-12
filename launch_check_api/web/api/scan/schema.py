from pydantic import BaseModel, HttpUrl

from launch_check_api.db.models.scan_model import ScanStatus

class ScanRequest(BaseModel):
    """Scan request model."""
    target_url: HttpUrl
    severity_levels: list[str] = ["medium", "high", "critical"]
    rate_limit: int = 100
    timeout: int = 10

class ScanResponse(BaseModel):
    """Scan response model."""
    scan_id: int
    target_url: str
    status: ScanStatus
    message: str
