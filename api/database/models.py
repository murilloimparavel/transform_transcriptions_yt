"""
Modelos SQLAlchemy para o banco de dados.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from api.database.database import Base
import enum


class JobStatus(str, enum.Enum):
    """Status de um job de processamento."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoStatus(str, enum.Enum):
    """Status de um vídeo."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingJob(Base):
    """Modelo para jobs de processamento."""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_type = Column(String, nullable=False)  # playlist, canal, documento
    source_id = Column(String, nullable=False)
    prompt_type = Column(String, nullable=False)  # faq, copywriting, framework
    output_language = Column(String, default="pt")
    preferred_languages = Column(String)  # JSON array de idiomas
    
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    total_videos = Column(Integer, default=0)
    processed_videos = Column(Integer, default=0)
    failed_videos = Column(Integer, default=0)
    
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relacionamentos
    videos = relationship("Video", back_populates="job", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="job", cascade="all, delete-orphan")


class Video(Base):
    """Modelo para vídeos processados."""
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    video_url = Column(String, nullable=False)
    video_id = Column(String)
    title = Column(String)
    
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.PENDING)
    transcription_path = Column(String)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    job = relationship("ProcessingJob", back_populates="videos")
    transcription = relationship("Transcription", back_populates="video", uselist=False)
    results = relationship("Result", back_populates="video")


class Transcription(Base):
    """Modelo para transcrições."""
    __tablename__ = "transcriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String, ForeignKey("videos.id"), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    language = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    video = relationship("Video", back_populates="transcription")


class Result(Base):
    """Modelo para resultados processados."""
    __tablename__ = "results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    video_id = Column(String, ForeignKey("videos.id"))
    
    result_type = Column(String, nullable=False)  # faq, copywriting, framework
    content = Column(Text)
    file_path = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    job = relationship("ProcessingJob", back_populates="results")
    video = relationship("Video", back_populates="results")

