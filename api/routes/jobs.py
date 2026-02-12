"""
Rotas para gerenciamento de jobs de processamento.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database.database import get_db
from api.database.models import ProcessingJob, JobStatus
from api.models.job import JobCreate, JobResponse, JobUpdate
from datetime import datetime
from api.services.job_service import JobService

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo job de processamento."""
    service = JobService(db)
    job = service.create_job(job_data)
    return JobResponse.model_validate(job)


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[JobStatus] = None,
    db: Session = Depends(get_db)
):
    """Lista todos os jobs."""
    service = JobService(db)
    jobs = service.list_jobs(skip=skip, limit=limit, status_filter=status_filter)
    return [JobResponse.from_orm(job) for job in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Obtém detalhes de um job."""
    service = JobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um job."""
    service = JobService(db)
    job = service.update_job(job_id, job_update)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Deleta um job."""
    service = JobService(db)
    success = service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job não encontrado")


@router.get("/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Obtém progresso de um job."""
    service = JobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    return {
        "job_id": job.id,
        "status": job.status.value,
        "progress": job.progress,
        "total_videos": job.total_videos,
        "processed_videos": job.processed_videos,
        "failed_videos": job.failed_videos
    }

