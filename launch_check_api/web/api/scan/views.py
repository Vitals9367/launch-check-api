import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Query

from launch_check_api.db.dao.scan_dao import ScanDAO
from launch_check_api.db.models.scan_model import ScanModel, ScanStatus
from launch_check_api.services.nuclei import NucleiError, NucleiService
from launch_check_api.web.api.scan.schema import ScanRequest, ScanResponse
from launch_check_api.tkq import broker
from taskiq import TaskiqDepends

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

@broker.task
async def run_scan(scan_id: int, scan_request: ScanRequest, scan_dao: Annotated[ScanDAO, TaskiqDepends()]) -> None:
    try:
        nuclei_service = NucleiService()
        
        await scan_dao.update_scan(
            scan_id,
            {"status": ScanStatus.IN_PROGRESS}
        )

        
        results = await nuclei_service.scan_target(
            target=str(scan_request.target_url),
            severity=scan_request.severity_levels,
            rate_limit=scan_request.rate_limit,
            timeout=scan_request.timeout,
        )
        
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.COMPLETED,
                "findings": results,
                "total_findings": len(results.get("findings", [])),
                "warnings": results.get("warnings"),
            }
        )
        
    except NucleiError as e:
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.FAILED,
                "error_message": str(e)
            }
        )
    except Exception as e:
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.FAILED,
                "error_message": f"Unexpected error: {str(e)}"
            }
        )