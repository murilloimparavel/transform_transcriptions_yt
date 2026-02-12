"""
Rotas para resultados processados.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from api.database.database import get_db
from api.services.result_service import ResultService
from api.database.models import Result
import os

router = APIRouter()


@router.get("/")
async def list_results(
    job_id: Optional[str] = None,
    video_id: Optional[str] = None,
    result_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista resultados com filtros opcionais."""
    service = ResultService(db)
    
    query = db.query(Result)
    
    if job_id:
        query = query.filter(Result.job_id == job_id)
    if video_id:
        query = query.filter(Result.video_id == video_id)
    if result_type:
        query = query.filter(Result.result_type == result_type)
    
    results = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "job_id": r.job_id,
            "video_id": r.video_id,
            "result_type": r.result_type,
            "file_path": r.file_path,
            "content_preview": r.content[:500] if r.content else None,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]


@router.get("/{result_id}")
async def get_result(result_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes de um resultado."""
    service = ResultService(db)
    result = service.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    
    return {
        "id": result.id,
        "job_id": result.job_id,
        "video_id": result.video_id,
        "result_type": result.result_type,
        "content": result.content,
        "file_path": result.file_path,
        "created_at": result.created_at.isoformat() if result.created_at else None
    }


@router.get("/{result_id}/download")
async def download_result(result_id: str, db: Session = Depends(get_db)):
    """Faz download do arquivo de resultado."""
    service = ResultService(db)
    result = service.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    
    if not result.file_path or not os.path.exists(result.file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    return FileResponse(
        result.file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(result.file_path)
    )

