from fastapi.routing import APIRouter

from launch_check_api.web.api import monitoring, scan

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
