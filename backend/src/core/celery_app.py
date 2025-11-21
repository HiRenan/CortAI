from celery import Celery
import os

# Configurações do Redis (usando env vars ou default localhost)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "cortai_worker",
    broker=BROKER_URL,
    backend=REDIS_URL,
    include=['src.core.tasks']  # Importante: registra as tasks
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Importa as tasks para garantir que sejam registradas
from src.core import tasks  # noqa

