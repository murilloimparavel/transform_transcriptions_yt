"""
Serviço para gerenciamento de vídeos.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from api.database.models import Video, VideoStatus


class VideoService:
    """Serviço para operações com vídeos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_video(self, video_id: str) -> Optional[Video]:
        """Obtém um vídeo por ID."""
        return self.db.query(Video).filter(Video.id == video_id).first()
    
    def get_videos_by_job(self, job_id: str) -> List[Video]:
        """Obtém todos os vídeos de um job."""
        return self.db.query(Video).filter(Video.job_id == job_id).all()
    
    def update_video_status(
        self,
        video_id: str,
        status: VideoStatus,
        error_message: Optional[str] = None
    ) -> Optional[Video]:
        """Atualiza status de um vídeo."""
        video = self.get_video(video_id)
        if not video:
            return None
        
        video.status = status
        if error_message:
            video.error_message = error_message
        
        self.db.commit()
        self.db.refresh(video)
        return video

