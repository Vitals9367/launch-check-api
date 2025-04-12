
from fastapi import APIRouter

from launch_check_api.services.nuclei import NucleiService

router = APIRouter()

@router.get("/")
async def scan_site():
    nuclei_service = NucleiService()

    await nuclei_service.update_templates()

    results = await nuclei_service.scan_target(
        target="https://www.launchcheck.io/",
        severity=["info", "low", "medium", "high", "critical"],
        rate_limit=100,
        timeout=10,
    )

    return results
