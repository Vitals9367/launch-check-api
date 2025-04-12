import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker
from taskiq_redis import RedisStreamBroker

from launch_check_api.settings import settings

# Configure Redis broker with settings
broker: AsyncBroker = RedisStreamBroker(
    url=settings.redis_url
)

# Use in-memory broker for tests
if settings.environment.lower() == "pytest":
    broker = InMemoryBroker()

# Initialize FastAPI integration
taskiq_fastapi.init(
    broker,
    "launch_check_api.web.application:get_app",
)
