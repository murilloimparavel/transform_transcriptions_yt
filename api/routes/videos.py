"""
Rotas para gerenciamento de vídeos.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from api.database.database import get_db
from api.services.video_service import VideoService
from api.database.models import Video

router = APIRouter()


@router.get("/")
async def list_videos(
    job_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista vídeos, opcionalmente filtrados por job."""
    service = VideoService(db)
    
    if job_id:
        videos = service.get_videos_by_job(job_id)
    else:
        videos = db.query(Video).offset(skip).limit(limit).all()
    
    return [
        {
            "id": v.id,
            "job_id": v.job_id,
            "video_url": v.video_url,
            "video_id": v.video_id,
            "title": v.title,
            "status": v.status.value,
            "error_message": v.error_message,
            "created_at": v.created_at.isoformat() if v.created_at else None
        }
        for v in videos
    ]


@router.get("/{video_id}")
async def get_video(video_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes de um vídeo."""
    service = VideoService(db)
    video = service.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    
    return {
        "id": video.id,
        "job_id": video.job_id,
        "video_url": video.video_url,
        "video_id": video.video_id,
        "title": video.title,
        "status": video.status.value,
        "transcription_path": video.transcription_path,
        "error_message": video.error_message,
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "updated_at": video.updated_at.isoformat() if video.updated_at else None
    }

