"""
API FastAPI principal.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from config.settings import settings
from api.database.database import init_db, engine
from api.database import models

# Importa rotas
from api.routes import jobs, videos, results, processing, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events da aplicação."""
    # Startup
    print("🚀 Inicializando API...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado")
    yield
    # Shutdown
    print("👋 Encerrando API...")


# Cria app FastAPI
app = FastAPI(
    title="YouTube Transcription Processor API",
    description="API para processamento de transcrições do YouTube com IA",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(processing.router, prefix="/api/processing", tags=["processing"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "YouTube Transcription Processor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

