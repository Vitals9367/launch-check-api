import logging
from fastapi import APIRouter, Depends

from launch_check_api.db.dao.scan_dao import ScanDAO
from launch_check_api.web.api.scan.schema import ScanRequest, ScanResponse
from launch_check_api.web.api.scan.tasks import run_scan

router = APIRouter()

logger= logging.getLogger(__name__)

@router.post("/")
async def scan_site(
    scan_request: ScanRequest,
    scan_dao: ScanDAO = Depends(),
) -> ScanResponse:
    """
    Create a new scan job and launch it as a background task.
    """
    scan = await scan_dao.create_scan(
        target_url=str(scan_request.target_url),
        severity_levels=scan_request.severity_levels,
        rate_limit=scan_request.rate_limit,
        timeout=scan_request.timeout,
    )
   
    await run_scan.kiq(scan.id, scan_request)
    
    return ScanResponse(
        scan_id=scan.id,
        target_url=scan.target_url,
        status=scan.status,
        message="Scan job created successfully"
    )

@router.get("/{scan_id}")
async def get_scan(scan_id: int, scan_dao: ScanDAO = Depends()):
    result = await scan_dao.get_scan_by_id(scan_id)
    return result.__dict__
