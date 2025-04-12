from fastapi.routing import APIRouter

from launch_check_api.web.api import dummy, echo, monitoring, scan

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(dummy.router, prefix="/dummy", tags=["dummy"])
api_router.include_router(scan.router, prefix="/scan", tags=["scan"])
