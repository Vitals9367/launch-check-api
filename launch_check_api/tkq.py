import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker, ZeroMQBroker

from launch_check_api.settings import settings

broker: AsyncBroker = ZeroMQBroker()

if settings.environment.lower() == "pytest":
    broker = InMemoryBroker()

taskiq_fastapi.init(
    broker,
    "launch_check_api.web.application:get_app",
)
