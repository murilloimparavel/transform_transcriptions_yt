"""
Rotas WebSocket para progresso em tempo real.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from api.database.database import get_db
from api.database.models import ProcessingJob
from typing import Dict, Set
import json
import asyncio

router = APIRouter()

# Armazena conexões WebSocket ativas
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Gerencia conexões WebSocket."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Conecta um cliente WebSocket."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Desconecta um cliente WebSocket."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def send_progress(self, job_id: str, data: dict):
        """Envia atualização de progresso para todos os clientes conectados."""
        if job_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(data)
                except:
                    disconnected.add(connection)
            
            # Remove conexões desconectadas
            for conn in disconnected:
                self.disconnect(conn, job_id)


manager = ConnectionManager()


@router.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint para receber atualizações de progresso de um job.
    """
    await manager.connect(websocket, job_id)
    
    try:
        # Envia estado inicial
        from api.database.database import SessionLocal
        db = SessionLocal()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        
        if job:
            await websocket.send_json({
                "type": "progress",
                "job_id": job_id,
                "status": job.status.value,
                "progress": job.progress,
                "total_videos": job.total_videos,
                "processed_videos": job.processed_videos,
                "failed_videos": job.failed_videos
            })
            db.close()
        
        # Mantém conexão aberta e envia atualizações periódicas
        while True:
            await asyncio.sleep(2)  # Atualiza a cada 2 segundos
            
            from api.database.database import SessionLocal
            db = SessionLocal()
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            
            if job:
                await websocket.send_json({
                    "type": "progress",
                    "job_id": job_id,
                    "status": job.status.value,
                    "progress": job.progress,
                    "total_videos": job.total_videos,
                    "processed_videos": job.processed_videos,
                    "failed_videos": job.failed_videos
                })
            
            # Se job foi concluído ou cancelado, envia mensagem final e fecha
            from api.database.models import JobStatus
            if job and job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                await websocket.send_json({
                    "type": "completed",
                    "job_id": job_id,
                    "status": job.status.value,
                    "final_progress": job.progress
                })
                db.close()
                break
            
            db.close()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(websocket, job_id)


# Função auxiliar para notificar progresso (chamada pelos workers)
async def notify_progress(job_id: str, progress_data: dict):
    """Notifica todos os clientes conectados sobre progresso."""
    await manager.send_progress(job_id, {
        "type": "progress",
        "job_id": job_id,
        **progress_data
    })

