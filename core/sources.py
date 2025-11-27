"""
Módulo para gerenciar fontes de vídeos (Playlists e Canais).
"""

from .sources_playlist import get_video_urls_from_playlist, save_playlist_to_json
from .sources_channel import (
    get_channel_videos,
    save_channel_videos_to_json,
    get_channel_id_by_name
)

__all__ = [
    'get_video_urls_from_playlist',
    'save_playlist_to_json',
    'get_channel_videos',
    'save_channel_videos_to_json',
    'get_channel_id_by_name'
]
