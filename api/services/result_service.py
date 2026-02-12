"""
Serviço para gerenciamento de resultados.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from api.database.models import Result


class ResultService:
    """Serviço para operações com resultados."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_result(self, result_id: str) -> Optional[Result]:
        """Obtém um resultado por ID."""
        return self.db.query(Result).filter(Result.id == result_id).first()
    
    def get_results_by_job(self, job_id: str) -> List[Result]:
        """Obtém todos os resultados de um job."""
        return self.db.query(Result).filter(Result.job_id == job_id).all()
    
    def get_results_by_video(self, video_id: str) -> List[Result]:
        """Obtém todos os resultados de um vídeo."""
        return self.db.query(Result).filter(Result.video_id == video_id).all()

