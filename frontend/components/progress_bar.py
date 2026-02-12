"""
Componente de barra de progresso para Streamlit.
"""
import streamlit as st
import time
from frontend.components.api_client import APIClient


def show_job_progress(job_id: str, api_client: APIClient, auto_refresh: bool = True):
    """
    Mostra barra de progresso de um job com atualização automática.
    
    Args:
        job_id: ID do job
        api_client: Cliente da API
        auto_refresh: Se deve atualizar automaticamente
    """
    progress_data = api_client.get_job_progress(job_id)
    
    if not progress_data:
        st.error("Não foi possível obter progresso do job.")
        return
    
    status = progress_data.get("status", "unknown")
    progress = progress_data.get("progress", 0)
    total_videos = progress_data.get("total_videos", 0)
    processed_videos = progress_data.get("processed_videos", 0)
    failed_videos = progress_data.get("failed_videos", 0)
    
    # Status com emoji
    status_emoji = {
        "pending": "⏸️",
        "processing": "⏳",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫"
    }
    
    st.subheader(f"{status_emoji.get(status, '❓')} Status: {status.upper()}")
    
    # Barra de progresso
    st.progress(progress / 100 if progress > 0 else 0)
    st.write(f"**Progresso:** {progress}%")
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Vídeos", total_videos)
    with col2:
        st.metric("Processados", processed_videos, delta=f"+{processed_videos}")
    with col3:
        st.metric("Falhas", failed_videos, delta=f"-{failed_videos}" if failed_videos > 0 else None)
    
    # Auto-refresh se estiver processando
    if auto_refresh and status == "processing":
        time.sleep(2)
        st.rerun()

