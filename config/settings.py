"""
Configurações centralizadas do sistema usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # API Keys
    api_key: str
    youtube_api_key: Optional[str] = None
    llm_model: str = "gemini-2.5-flash"
    
    # Proxies
    use_proxies: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/app.db"
    
    # Redis (para Celery)
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Processing
    max_retries: int = 3
    chunk_size: int = 10000
    max_workers: int = 5
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Frontend
    frontend_port: int = 8501
    
    # Paths
    data_dir: str = "data"
    transcriptions_dir: str = "data/transcriptions"
    processed_dir: str = "data/processed"
    logs_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global de settings
settings = Settings()

