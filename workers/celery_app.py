"""
Configuração do Celery para processamento assíncrono.
"""
from celery import Celery
from config.settings import settings

# Cria app Celery
celery_app = Celery(
    "transcription_processor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configuração
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora
    task_soft_time_limit=3300,  # 55 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["workers"])

