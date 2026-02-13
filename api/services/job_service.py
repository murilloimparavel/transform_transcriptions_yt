"""
Serviço para gerenciamento de jobs.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from api.database.models import ProcessingJob, JobStatus
from api.models.job import JobCreate, JobUpdate
from datetime import datetime


class JobService:
    """Serviço para operações com jobs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(self, job_data: JobCreate) -> ProcessingJob:
        """Cria um novo job."""
        job = ProcessingJob(
            source_type=job_data.source_type,
            source_id=job_data.source_id,
            prompt_type=job_data.prompt_type,
            output_language=job_data.output_language,
            preferred_languages=job_data.preferred_languages,
            status=JobStatus.PENDING
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Obtém um job por ID."""
        return self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    
    def list_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[JobStatus] = None
    ) -> List[ProcessingJob]:
        """Lista jobs com filtros."""
        query = self.db.query(ProcessingJob)
        
        if status_filter:
            query = query.filter(ProcessingJob.status == status_filter)
        
        return query.order_by(ProcessingJob.created_at.desc()).offset(skip).limit(limit).all()
    
    def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[ProcessingJob]:
        """Atualiza um job."""
        job = self.get_job(job_id)
        if not job:
            return None
        
        if job_update.status is not None:
            job.status = job_update.status
            if job_update.status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
        
        if job_update.progress is not None:
            job.progress = job_update.progress
        
        if job_update.processed_videos is not None:
            job.processed_videos = job_update.processed_videos
        
        if job_update.failed_videos is not None:
            job.failed_videos = job_update.failed_videos
        
        if job_update.error_message is not None:
            job.error_message = job_update.error_message
        
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def delete_job(self, job_id: str) -> bool:
        """Deleta um job."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        self.db.delete(job)
        self.db.commit()
        return True

