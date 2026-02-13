"""
Modelos Pydantic para Jobs.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from api.database.models import JobStatus


class JobCreate(BaseModel):
    """Modelo para criação de job."""
    source_type: str = Field(..., description="Tipo de fonte: playlist, canal, documento")
    source_id: str = Field(..., description="ID ou URL da fonte")
    prompt_type: str = Field(..., description="Tipo de prompt: faq, copywriting, framework")
    output_language: str = Field(default="pt", description="Idioma de saída")
    preferred_languages: Optional[str] = Field(None, description="Idiomas preferidos (JSON array)")


class JobUpdate(BaseModel):
    """Modelo para atualização de job."""
    status: Optional[JobStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    processed_videos: Optional[int] = None
    failed_videos: Optional[int] = None
    error_message: Optional[str] = None


class JobResponse(BaseModel):
    """Modelo de resposta de job."""
    id: str
    source_type: str
    source_id: str
    prompt_type: str
    output_language: str
    preferred_languages: Optional[str]
    status: str  # JobStatus.value como string
    progress: int
    total_videos: int
    processed_videos: int
    failed_videos: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    @classmethod
    def from_orm(cls, obj):
        """Cria instância a partir de objeto ORM."""
        data = {
            "id": obj.id,
            "source_type": obj.source_type,
            "source_id": obj.source_id,
            "prompt_type": obj.prompt_type,
            "output_language": obj.output_language,
            "preferred_languages": obj.preferred_languages,
            "status": obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            "progress": obj.progress,
            "total_videos": obj.total_videos,
            "processed_videos": obj.processed_videos,
            "failed_videos": obj.failed_videos,
            "error_message": obj.error_message,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "completed_at": obj.completed_at
        }
        return cls(**data)
    
    class Config:
        from_attributes = True

