"""
Tarefas Celery para processamento assíncrono.
"""
import os
import sys
import logging
from typing import List, Optional
from workers.celery_app import celery_app
from api.database.database import SessionLocal
from api.database.models import ProcessingJob, Video, Transcription, Result, JobStatus, VideoStatus
from api.services.job_service import JobService
from datetime import datetime
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa código existente
from core.transcription import download_transcription
from core.processing import process_transcription, load_prompt
from core.framework_processor import process_transcription_framework
from core.n8n_processor import process_n8n_framework
from core.prd_processor import process_prd_framework


@celery_app.task(bind=True, name="workers.tasks.process_video")
def process_video_task(
    self,
    job_id: str,
    video_url: str,
    video_id: str,
    video_title: str,
    preferred_languages: Optional[List[str]],
    prompt_type: str,
    output_language: str
):
    """
    Processa um único vídeo de forma assíncrona.
    
    Args:
        job_id: ID do job
        video_url: URL do vídeo
        video_id: ID do vídeo
        video_title: Título do vídeo
        preferred_languages: Lista de idiomas preferidos
        prompt_type: Tipo de prompt (faq, copywriting, framework)
        output_language: Idioma de saída
    """
    db = SessionLocal()
    try:
        # Atualiza status do vídeo para downloading
        video = db.query(Video).filter(
            Video.job_id == job_id,
            Video.video_id == video_id
        ).first()
        
        if not video:
            video = Video(
                job_id=job_id,
                video_url=video_url,
                video_id=video_id,
                title=video_title,
                status=VideoStatus.DOWNLOADING
            )
            db.add(video)
            db.commit()
            db.refresh(video)
        else:
            video.status = VideoStatus.DOWNLOADING
            db.commit()
        
        # Download da transcrição
        try:
            # Converte preferred_languages de string JSON para lista se necessário
            if isinstance(preferred_languages, str):
                try:
                    preferred_languages = json.loads(preferred_languages)
                except:
                    preferred_languages = [preferred_languages] if preferred_languages else None
            
            transcription_path = download_transcription(
                video_url,
                preferred_languages=preferred_languages,
                max_retries=3
            )
            
            if not transcription_path:
                video.status = VideoStatus.FAILED
                video.error_message = "Falha ao baixar transcrição"
                db.commit()
                return {"status": "failed", "error": "Transcrição não disponível"}
            
            # Salva transcrição no banco
            with open(transcription_path, 'r', encoding='utf-8') as f:
                transcription_content = f.read()
            
            transcription = Transcription(
                video_id=video.id,
                content=transcription_content,
                language=preferred_languages[0] if preferred_languages else "unknown"
            )
            db.add(transcription)
            video.transcription_path = transcription_path
            video.status = VideoStatus.PROCESSING
            db.commit()
            
        except Exception as e:
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            db.commit()
            return {"status": "failed", "error": str(e)}
        
        # Processamento com IA
        try:
            video.status = VideoStatus.PROCESSING
            db.commit()
            
            if prompt_type == "framework":
                # Processamento framework completo
                output_path = process_transcription_framework(
                    transcription_path,
                    output_language
                )
            elif prompt_type == "prd":
                # Processamento de PRD BMAD
                output_path = process_prd_framework(
                    transcription_path,
                    output_language
                )
            else:
                # Processamento normal (FAQ ou Copywriting)
                process_transcription(
                    transcription_path,
                    prompt_type,
                    output_language
                )
                # Determina caminho de saída
                base_name = os.path.splitext(os.path.basename(transcription_path))[0]
                output_path = os.path.join(
                    'data', 'processed',
                    f"{base_name}_{prompt_type}_{output_language}_processed.txt"
                )
            
            # Salva resultado no banco
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    result_content = f.read()
                
                result = Result(
                    job_id=job_id,
                    video_id=video.id,
                    result_type=prompt_type,
                    content=result_content,
                    file_path=output_path
                )
                db.add(result)
                video.status = VideoStatus.COMPLETED
                db.commit()
                
                return {
                    "status": "completed",
                    "video_id": video_id,
                    "result_path": output_path
                }
            else:
                video.status = VideoStatus.FAILED
                video.error_message = "Arquivo de resultado não encontrado"
                db.commit()
                return {"status": "failed", "error": "Resultado não gerado"}
                
        except Exception as e:
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            db.commit()
            return {"status": "failed", "error": str(e)}
            
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="workers.tasks.process_job")
def process_job_task(self, job_id: str):
    """
    Processa um job completo (múltiplos vídeos).
    
    Args:
        job_id: ID do job
    """
    db = SessionLocal()
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            return {"status": "failed", "error": "Job não encontrado"}
        
        # Atualiza status para processing
        job.status = JobStatus.PROCESSING
        db.commit()
        
        # Obtém lista de vídeos baseado no tipo de fonte
        videos = []
        preferred_languages = json.loads(job.preferred_languages) if job.preferred_languages else None
        
        if job.source_type == "playlist":
            try:
                from core.sources import get_playlist_videos
                videos = get_playlist_videos(job.source_id, preferred_languages)
            except ImportError:
                # Fallback para função antiga
                from core.sources_playlist import get_video_urls_from_playlist
                from core.transcription import get_video_id
                video_urls = get_video_urls_from_playlist(job.source_id)
                videos = []
                for url in video_urls:
                    video_id = get_video_id(url)
                    videos.append({
                        "url": url,
                        "id": video_id,
                        "video_id": video_id,
                        "title": f"Video {video_id}"
                    })
        elif job.source_type == "canal":
            try:
                from core.sources import get_channel_videos
                videos = get_channel_videos(job.source_id)
            except ImportError:
                # Fallback para função antiga
                from core.sources_channel import get_channel_videos as get_channel_videos_internal
                from core.transcription import get_video_id
                video_infos = get_channel_videos_internal(job.source_id)
                videos = []
                for info in video_infos:
                    video_id = get_video_id(info["url"])
                    videos.append({
                        "url": info["url"],
                        "id": video_id,
                        "video_id": video_id,
                        "title": info.get("title", "Sem título")
                    })
        elif job.source_type == "documento":
            # Para documentos, processa diretamente
            from core.document_extractor import extract_text_from_source
            try:
                text, source_type = extract_text_from_source(job.source_id)
                # Cria um "vídeo" virtual para o documento
                videos = [{
                    "url": job.source_id,
                    "id": os.path.basename(job.source_id),
                    "video_id": os.path.basename(job.source_id),
                    "title": os.path.basename(job.source_id),
                    "is_document": True
                }]
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error_message = f"Erro ao processar documento: {str(e)}"
                db.commit()
                return {"status": "failed", "error": str(e)}
        elif job.source_type == "n8n" or job.source_type == "json":
             videos = [{
                "url": job.source_id,
                "id": os.path.basename(job.source_id),
                "video_id": os.path.basename(job.source_id),
                "title": "N8N Workflow",
                "is_n8n": True
            }]
        
        if not videos:
            job.status = JobStatus.FAILED
            job.error_message = "Nenhum vídeo encontrado"
            db.commit()
            return {"status": "failed", "error": "Nenhum vídeo encontrado"}
        
        # Atualiza total de vídeos
        job.total_videos = len(videos)
        db.commit()
        
        # Processa cada vídeo
        processed = 0
        failed = 0
        
        for idx, video_data in enumerate(videos):
            # Atualiza progresso
            progress = int((idx / len(videos)) * 100)
            job.progress = progress
            job.processed_videos = processed
            job.failed_videos = failed
            db.commit()
            
            # Processa vídeo
            video_url = video_data.get("url") or video_data.get("video_url") or str(video_data)
            video_id = video_data.get("id") or video_data.get("video_id", "")
            video_title = video_data.get("title", "Sem título")
            
            # Se for n8n
            if video_data.get("is_n8n"):
                try:
                    from core.n8n_processor import process_n8n_framework
                    
                    output_path = process_n8n_framework(job.source_id, job.output_language)
                    
                    if os.path.exists(output_path):
                        with open(output_path, 'r', encoding='utf-8') as f:
                            result_content = f.read()
                        
                        result = Result(
                            job_id=job_id,
                            result_type="n8n_framework",
                            content=result_content,
                            file_path=output_path
                        )
                        db.add(result)
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"Erro ao processar n8n: {e}")
                continue

            # Se for documento, processa diretamente
            if video_data.get("is_document"):
                # Processa documento diretamente
                try:
                    from core.document_extractor import extract_text_from_source
                    from core.processing import process_transcription
                    from core.framework_processor import process_transcription_framework
                    import tempfile
                    
                    text, _ = extract_text_from_source(job.source_id)
                    
                    # Salva em arquivo temporário
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                        f.write(text)
                        temp_path = f.name
                    
                    # Processa
                    if job.prompt_type == "framework":
                        output_path = process_transcription_framework(temp_path, job.output_language)
                    elif job.prompt_type == "prd":
                        output_path = process_prd_framework(temp_path, job.output_language)
                    else:
                        process_transcription(temp_path, job.prompt_type, job.output_language)
                        base_name = os.path.splitext(os.path.basename(temp_path))[0]
                        output_path = os.path.join(
                            'data', 'processed',
                            f"{base_name}_{job.prompt_type}_{job.output_language}_processed.txt"
                        )
                    
                    # Salva resultado
                    if os.path.exists(output_path):
                        with open(output_path, 'r', encoding='utf-8') as f:
                            result_content = f.read()
                        
                        result = Result(
                            job_id=job_id,
                            result_type=job.prompt_type,
                            content=result_content,
                            file_path=output_path
                        )
                        db.add(result)
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"Erro ao processar documento: {e}")
            else:
                # Processa vídeo normalmente
                result = process_video_task.delay(
                    job_id=job_id,
                    video_url=video_url,
                    video_id=video_id,
                    video_title=video_title,
                    preferred_languages=preferred_languages,
                    prompt_type=job.prompt_type,
                    output_language=job.output_language
                )
                
                # Aguarda conclusão (ou pode ser assíncrono)
                try:
                    task_result = result.get(timeout=3600)
                    if task_result.get("status") == "completed":
                        processed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logging.error(f"Erro ao processar vídeo {video_id}: {e}")
        
        # Finaliza job
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.processed_videos = processed
        job.failed_videos = failed
        job.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "processed": processed,
            "failed": failed,
            "total": len(videos)
        }
        
    except Exception as e:
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

