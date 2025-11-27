import os
import json
from datetime import datetime

class ProgressManager:
    """Gerencia o progresso de processamento de playlists e canais."""

    def __init__(self, progress_file="data/progress/progress.json"):
        self.progress_file = progress_file
        self.ensure_directory_exists()

    def ensure_directory_exists(self):
        """Garante que o diretório de progresso existe."""
        directory = os.path.dirname(self.progress_file)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_progress(self):
        """Carrega o progresso atual do arquivo JSON."""
        if not os.path.exists(self.progress_file):
            return None

        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar progresso: {e}")
            return None

    def save_progress(self, source_type, source_id, language, videos, current_index=0, completed=False, prompt_type=None, output_language=None):
        """
        Salva o progresso atual.

        Args:
            source_type: 'playlist' ou 'canal'
            source_id: URL da playlist ou ID do canal
            language: Código do idioma das legendas (ou lista de idiomas preferidos)
            videos: Lista de vídeos (URLs ou dicts)
            current_index: Índice do próximo vídeo a processar
            completed: Se o processamento foi concluído
            prompt_type: Tipo de prompt ('faq' ou 'copywriting')
            output_language: Idioma do output final da IA
        """
        progress_data = {
            "source_type": source_type,
            "source_id": source_id,
            "language": language,
            "videos": videos,
            "current_index": current_index,
            "total_videos": len(videos),
            "completed": completed,
            "prompt_type": prompt_type,
            "output_language": output_language,
            "last_update": datetime.now().isoformat()
        }

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=4)

    def clear_progress(self):
        """Remove o arquivo de progresso."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)

    def has_incomplete_task(self):
        """Verifica se existe uma tarefa incompleta."""
        progress = self.get_progress()
        if progress is None:
            return False
        return not progress.get("completed", False)

    def get_pending_videos(self):
        """Retorna os vídeos que ainda precisam ser processados."""
        progress = self.get_progress()
        if progress is None:
            return []

        current_index = progress.get("current_index", 0)
        videos = progress.get("videos", [])

        return videos[current_index:]

    def get_transcription_path(self, video_url_or_id):
        """
        Verifica se a transcrição já existe para um vídeo.

        Args:
            video_url_or_id: URL do vídeo ou dict com info do vídeo

        Returns:
            Caminho do arquivo se existir, None caso contrário
        """
        # Extrai o ID do vídeo
        if isinstance(video_url_or_id, dict):
            video_url = video_url_or_id.get('url', '')
        else:
            video_url = video_url_or_id

        try:
            from .transcription import get_video_id
            video_id = get_video_id(video_url)
        except:
            return None

        # Verifica se existe algum arquivo de transcrição para esse vídeo
        transcriptions_dir = os.path.join("data", "transcriptions")
        if not os.path.exists(transcriptions_dir):
            return None

        for filename in os.listdir(transcriptions_dir):
            if filename.startswith(video_id + "_") and filename.endswith(".txt"):
                return os.path.join(transcriptions_dir, filename)

        return None

    def mark_video_completed(self):
        """Marca o vídeo atual como concluído e avança o índice."""
        progress = self.get_progress()
        if progress is None:
            return

        current_index = progress.get("current_index", 0) + 1
        total_videos = progress.get("total_videos", 0)

        # Verifica se todos os vídeos foram processados
        completed = current_index >= total_videos

        self.save_progress(
            source_type=progress["source_type"],
            source_id=progress["source_id"],
            language=progress["language"],
            videos=progress["videos"],
            current_index=current_index,
            completed=completed
        )

    def get_progress_summary(self):
        """Retorna um resumo do progresso para exibição."""
        progress = self.get_progress()
        if progress is None:
            return None

        total = progress.get("total_videos", 0)
        current = progress.get("current_index", 0)
        percentage = (current / total * 100) if total > 0 else 0

        return {
            "source_type": progress.get("source_type"),
            "source_id": progress.get("source_id"),
            "language": progress.get("language"),
            "current_index": current,
            "total_videos": total,
            "percentage": percentage,
            "completed": progress.get("completed", False),
            "last_update": progress.get("last_update")
        }
