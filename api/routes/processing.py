"""
Rotas para processamento.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.database.database import get_db
from api.database.models import ProcessingJob, JobStatus
from api.services.job_service import JobService
from workers.tasks import process_job_task

router = APIRouter()


@router.post("/start/{job_id}")
async def start_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inicia processamento de um job de forma assíncrona.
    """
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Job já está em processamento ou concluído. Status: {job.status.value}"
        )
    
    # Inicia processamento assíncrono
    try:
        # Usa Celery se disponível, senão processa em background
        try:
            task = process_job_task.delay(job_id)
            return {
                "message": "Processamento iniciado",
                "job_id": job_id,
                "task_id": task.id,
                "status": "queued"
            }
        except Exception as e:
            # Fallback: processa em background thread
            background_tasks.add_task(process_job_task, job_id)
            return {
                "message": "Processamento iniciado em background",
                "job_id": job_id,
                "status": "processing"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar processamento: {str(e)}")


@router.post("/cancel/{job_id}")
async def cancel_processing(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancela processamento de um job.
    """
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível cancelar job com status: {job.status.value}"
        )
    
    job.status = JobStatus.CANCELLED
    db.commit()
    
    return {
        "message": "Processamento cancelado",
        "job_id": job_id
    }
