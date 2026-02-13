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
from .sources_playlist import (
    save_playlist_to_json,
    get_video_urls_from_playlist
)
from .sources_channel import (
    save_channel_videos_to_json,
    get_channel_id_by_name
)
from .sources import (
    get_playlist_videos,
    get_channel_videos
)
from .framework_processor import process_transcription_framework
from .agent_builder_processor import process_transcription_agent_builder
from .agent_consolidator import consolidate_agent_builder_outputs, AgentConsolidator
from .n8n_processor import process_n8n_framework
from .prd_processor import process_prd_framework

__all__ = [
    'get_video_id',
    'get_available_transcripts',
    'download_transcription',
    'process_transcription',
    'load_prompt',
    'ProgressManager',
    'save_playlist_to_json',
    'save_channel_videos_to_json',
    'get_channel_id_by_name',
    'get_playlist_videos',
    'get_channel_videos',
    'get_video_urls_from_playlist',
    'process_transcription_framework',
    'process_transcription_agent_builder',
    'consolidate_agent_builder_outputs',
    'AgentConsolidator',
    'process_n8n_framework',
    'process_prd_framework'
]
