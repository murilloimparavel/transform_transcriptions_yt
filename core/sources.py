"""
Funções auxiliares para obter listas de vídeos de diferentes fontes.
Retorna formato padronizado para uso na API.
"""
from typing import List, Dict, Optional
from core.transcription import get_video_id


def get_playlist_videos(playlist_url: str, preferred_languages: Optional[List[str]] = None) -> List[Dict]:
    """
    Obtém lista de vídeos de uma playlist.
    
    Args:
        playlist_url: URL da playlist
        preferred_languages: Lista de idiomas preferidos (não usado aqui, mas mantido para compatibilidade)
    
    Returns:
        Lista de dicionários com informações dos vídeos
    """
    from core.sources_playlist import get_video_urls_from_playlist
    
    video_urls = get_video_urls_from_playlist(playlist_url)
    
    videos = []
    for url in video_urls:
        video_id = get_video_id(url)
        videos.append({
            "url": url,
            "id": video_id,
            "video_id": video_id,
            "title": f"Video {video_id}"  # Título será atualizado depois
        })
    
    return videos


def get_channel_videos(channel_id: str) -> List[Dict]:
    """
    Obtém lista de vídeos de um canal.
    
    Args:
        channel_id: ID do canal
    
    Returns:
        Lista de dicionários com informações dos vídeos
    """
    from core.sources_channel import get_channel_videos as get_channel_videos_internal
    
    video_infos = get_channel_videos_internal(channel_id)
    
    videos = []
    for info in video_infos:
        video_id = get_video_id(info["url"])
        videos.append({
            "url": info["url"],
            "id": video_id,
            "video_id": video_id,
            "title": info.get("title", "Sem título"),
            "published_at": info.get("publishedAt"),
            "duration_seconds": info.get("duration_seconds", 0)
        })
    
    return videos
