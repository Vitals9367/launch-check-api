from datetime import datetime
import logging
import traceback
from typing import Annotated

from launch_check_api.db.dao.scan_dao import ScanDAO
from launch_check_api.db.models.scan_model import ScanStatus
from launch_check_api.services.nuclei import NucleiError, NucleiService
from launch_check_api.web.api.scan.schema import ScanRequest
from launch_check_api.tkq import broker
from taskiq import TaskiqDepends

logger = logging.getLogger(__name__)

@broker.task
async def run_scan(
    scan_id: int, 
    scan_request: ScanRequest, 
    scan_dao: Annotated[ScanDAO, TaskiqDepends()],
    nuclei_service: Annotated[NucleiService, TaskiqDepends()]
) -> None:
    """
    Execute a security scan task.
    
    Args:
        scan_id: The ID of the scan in the database
        scan_request: The scan request parameters
        scan_dao: Data access object for scan operations
    """
    logger.info(
        "Starting scan task | ID: %d | Target: %s | Severity Levels: %s",
        scan_id,
        scan_request.target_url,
        scan_request.severity_levels,
    )
    
    try:
        # Initialize Nuclei service
        logger.debug("Initializing Nuclei service")
        
        logger.info("Nuclei service initialized successfully")
        
        # Update scan status to in progress
        logger.debug("Updating scan status to IN_PROGRESS")
        await scan_dao.update_scan(
            scan_id,
            {"status": ScanStatus.IN_PROGRESS}
        )
        logger.info("Scan status updated to IN_PROGRESS")
        
        # Execute the scan
        logger.info(
            "Starting Nuclei scan | Rate Limit: %d | Timeout: %d",
            scan_request.rate_limit,
            scan_request.timeout,
        )
        results = await nuclei_service.scan_target(
            target=str(scan_request.target_url),
            severity=scan_request.severity_levels,
            rate_limit=scan_request.rate_limit,
            timeout=scan_request.timeout,
        )
        
        # Log scan results summary
        findings_count = len(results.get("findings", []))
        has_warnings = bool(results.get("warnings"))
        logger.info(
            "Scan completed | Findings: %d | Has Warnings: %s",
            findings_count,
            has_warnings,
        )
        
        if has_warnings:
            logger.warning("Scan warnings: %s", results.get("warnings"))
            
        # Update scan with results
        logger.debug("Updating scan with results in database")
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.COMPLETED,
                "findings": results,
                "total_findings": findings_count,
                "warnings": results.get("warnings"),
                "completed_at": datetime.now()
            }
        )
        logger.info("Scan results saved successfully to database")
        
    except NucleiError as e:
        logger.error(
            "Nuclei error occurred | Scan ID: %d | Error: %s",
            scan_id,
            str(e),
            exc_info=True,
        )
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.FAILED,
                "error_message": str(e)
            }
        )
        logger.info("Scan status updated to FAILED due to Nuclei error")
        
    except Exception as e:
        # Get full traceback for unexpected errors
        error_trace = traceback.format_exc()
        logger.error(
            "Unexpected error in scan task | Scan ID: %d | Error: %s\nTraceback:\n%s",
            scan_id,
            str(e),
            error_trace,
        )
        await scan_dao.update_scan(
            scan_id,
            {
                "status": ScanStatus.FAILED,
                "error_message": f"Unexpected error: {str(e)}"
            }
        )
        logger.info("Scan status updated to FAILED due to unexpected error")
    
    finally:
        logger.info(
            "Scan task completed | ID: %d | Target: %s",
            scan_id,
            scan_request.target_url,
        )