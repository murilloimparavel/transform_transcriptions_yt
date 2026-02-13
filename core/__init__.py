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
from .framework_processor import process_transcription_framework
from .agent_builder_processor import process_transcription_agent_builder
from .agent_consolidator import consolidate_agent_builder_outputs, AgentConsolidator

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
    'process_transcription_framework',
    'process_transcription_agent_builder',
    'consolidate_agent_builder_outputs',
    'AgentConsolidator'
]
