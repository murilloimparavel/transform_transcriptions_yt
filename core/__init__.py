"""
Core functionality for YouTube Transcription Processor.
"""

from .transcription import (
    get_video_id,
    get_available_transcripts,
    download_transcription
)
from .processing import (
    process_transcription,
    load_prompt
)
from .progress import ProgressManager
from .sources import (
    save_playlist_to_json,
    save_channel_videos_to_json,
    get_channel_id_by_name
)

__all__ = [
    'get_video_id',
    'get_available_transcripts',
    'download_transcription',
    'process_transcription',
    'load_prompt',
    'ProgressManager',
    'save_playlist_to_json',
    'save_channel_videos_to_json',
    'get_channel_id_by_name'
]
