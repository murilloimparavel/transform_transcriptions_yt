import os
import json
import time
from termcolor import colored, cprint
from dotenv import load_dotenv
from core import (
    save_channel_videos_to_json,
    get_channel_id_by_name,
    save_playlist_to_json,
    download_transcription,
    process_transcription,
    ProgressManager
)

# Carrega as variáveis do .env
load_dotenv()

# Inicializa o gerenciador de progresso
progress_manager = ProgressManager()

def ensure_directory_exists(directory):
    """Verifica se um diretório existe e o cria se não existir."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        cprint(f"Diretório '{directory}' criado.", "green")

def download_transcriptions(source_type, source_id, language, prompt_type, output_language, resume=False):
    """
    Gerencia o download de transcrições, seja de uma playlist ou canal.

    Args:
        source_type: 'playlist' ou 'canal'
        source_id: URL da playlist ou ID do canal
        language: Lista de idiomas preferidos para legendas
        prompt_type: 'faq' ou 'copywriting'
        output_language: Idioma do output final ('pt' ou 'en')
        resume: Se deve retomar do progresso salvo
    """
    playlists_dir = os.path.join('data', 'playlists')
    ensure_directory_exists(playlists_dir)

    if not resume:
        # Nova execução - busca e salva os vídeos
        if source_type == "playlist":
            json_file = os.path.join(playlists_dir, 'playlist_videos.json')
            cprint("Iniciando o download das transcrições da playlist...", "cyan", attrs=["bold"])
            # Converte lista de idiomas para string para salvar no JSON antigo
            lang_str = language[0] if isinstance(language, list) else language
            save_playlist_to_json(source_id, lang_str, json_file)
        elif source_type == "canal":
            json_file = os.path.join(playlists_dir, 'channel_videos.json')
            cprint("Iniciando o download das transcrições do canal...", "cyan", attrs=["bold"])
            save_channel_videos_to_json(source_id, json_file)
        else:
            cprint("Tipo de fonte desconhecido.", "red", attrs=["bold"])
            return
    else:
        # Retomando execução - usa os dados do progresso
        cprint("Retomando processamento interrompido...", "cyan", attrs=["bold"])

    process_videos_from_json_with_progress(source_type, source_id, language, prompt_type, output_language, resume)

def process_videos_from_json_with_progress(source_type, source_id, language, prompt_type, output_language, resume=False):
    """
    Processa os vídeos com gerenciamento de progresso.

    Args:
        source_type: 'playlist' ou 'canal'
        source_id: URL da playlist ou ID do canal
        language: Lista de idiomas preferidos para legendas
        prompt_type: 'faq' ou 'copywriting'
        output_language: Idioma do output final
        resume: Se está retomando uma execução anterior
    """
    if resume:
        # Carrega do progresso salvo
        progress = progress_manager.get_progress()
        if not progress:
            cprint("Nenhum progresso encontrado para retomar.", "red", attrs=["bold"])
            return

        videos = progress["videos"]
        current_index = progress["current_index"]
        # Garante valores padrão se não existir no progresso
        prompt_type = progress.get("prompt_type") or "copywriting"
        output_language = progress.get("output_language") or "pt"
        cprint(f"\n📊 Retomando: {current_index}/{len(videos)} vídeos já processados", "cyan", attrs=["bold"])
        cprint(f"📝 Tipo de prompt: {prompt_type.upper()}", "cyan")
        cprint(f"🌍 Idioma de saída: {output_language.upper()}", "cyan")
    else:
        # Carrega do JSON de playlists
        playlists_dir = os.path.join('data', 'playlists')
        if source_type == "playlist":
            json_file = os.path.join(playlists_dir, 'playlist_videos.json')
        else:
            json_file = os.path.join(playlists_dir, 'channel_videos.json')

        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        videos = data.get('videos', [])
        current_index = 0

        if not videos:
            cprint("Nenhum vídeo encontrado para processar.", "red", attrs=["bold"])
            return

        # Salva o progresso inicial
        progress_manager.save_progress(source_type, source_id, language, videos, current_index,
                                     prompt_type=prompt_type, output_language=output_language)

    from_playlist = (source_type == "playlist")
    total_videos = len(videos)

    # Estatísticas de processamento
    stats = {
        "total": total_videos,
        "processed": 0,
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "failed_videos": []
    }

    # Processa os vídeos a partir do índice atual
    for idx in range(current_index, total_videos):
        video_info = videos[idx]

        try:
            if from_playlist:
                video_url = video_info
                video_desc = video_url
            else:
                video_url = video_info['url']
                video_desc = video_info['title']

            cprint(f"\n[{idx + 1}/{total_videos}] Processando: {video_desc}", "yellow")

            # Verifica se a transcrição já existe
            existing_transcription = progress_manager.get_transcription_path(video_info)
            if existing_transcription:
                cprint(f"⏭️  Transcrição já existe: {existing_transcription}", "blue")
                stats["skipped"] += 1
                progress_manager.mark_video_completed()
                continue

            # Passa lista de idiomas preferidos (ou None para qualquer)
            if language is None:
                preferred_langs = None
            elif isinstance(language, list):
                preferred_langs = language
            else:
                preferred_langs = [language]

            file_path = download_transcription(video_url, preferred_langs, max_retries=3)

            if file_path:
                used_lang = os.path.splitext(file_path)[0].split("_")[-1]
                cprint(f"✅ Transcrição salva [{used_lang}] em {file_path}", "green", attrs=["bold"])
                stats["success"] += 1
            else:
                cprint(f"⚠️  Vídeo sem transcrição disponível - pulando", "yellow", attrs=["bold"])
                stats["failed"] += 1
                stats["failed_videos"].append({
                    "url": video_url,
                    "index": idx + 1
                })

            stats["processed"] += 1
            # Atualiza o progresso
            progress_manager.mark_video_completed()

        except KeyboardInterrupt:
            cprint("\n\n⚠️  Processamento interrompido pelo usuário!", "yellow", attrs=["bold"])
            cprint("Execute o programa novamente para continuar de onde parou.", "cyan")
            # Mostra estatísticas parciais
            show_stats(stats)
            return
        except Exception as e:
            cprint(f"❌ Erro ao processar o vídeo {video_desc}: {e}", "red")
            stats["failed"] += 1
            stats["failed_videos"].append({
                "url": video_url if 'video_url' in locals() else "URL desconhecida",
                "index": idx + 1,
                "error": str(e)
            })
            # Mesmo com erro, marca como processado para não travar
            progress_manager.mark_video_completed()

    # Processamento concluído
    cprint(f"\n🎉 Todos os {total_videos} vídeos foram processados!", "green", attrs=["bold"])
    progress_manager.save_progress(source_type, source_id, language, videos, total_videos, completed=True,
                                  prompt_type=prompt_type, output_language=output_language)

    # Mostra estatísticas finais
    show_stats(stats)

    # Processa as transcrições com o prompt selecionado
    cprint(f"\n🤖 Processando transcrições com prompt: {prompt_type.upper()}", "cyan", attrs=["bold"])
    cprint(f"🌍 Idioma de saída: {output_language.upper()}", "cyan", attrs=["bold"])
    process_all_transcriptions(prompt_type, output_language)

def show_stats(stats):
    """Exibe estatísticas do processamento"""
    cprint("\n" + "="*60, "cyan")
    cprint("📊 ESTATÍSTICAS DO PROCESSAMENTO", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")

    cprint(f"Total de vídeos: {stats['total']}", "white")
    cprint(f"✅ Sucessos: {stats['success']}", "green")
    cprint(f"⏭️  Pulados (já existiam): {stats['skipped']}", "blue")
    cprint(f"⚠️  Falharam: {stats['failed']}", "yellow")

    if stats['failed_videos']:
        cprint(f"\n📋 Vídeos que falharam ({len(stats['failed_videos'])}):", "yellow", attrs=["bold"])
        for failed in stats['failed_videos']:
            cprint(f"  [{failed['index']}] {failed['url']}", "yellow")
            if 'error' in failed:
                cprint(f"      Erro: {failed['error']}", "red")

    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    cprint(f"\n✨ Taxa de sucesso: {success_rate:.1f}%", "green", attrs=["bold"])
    cprint("="*60 + "\n", "cyan")


def process_all_transcriptions(prompt_type="copywriting", output_language="pt"):
    """
    Processa todos os arquivos de transcrição presentes na pasta 'data/transcriptions'.

    Args:
        prompt_type: 'faq', 'copywriting' ou 'framework'
        output_language: Idioma do output ('pt' ou 'en')
    """
    transcriptions_dir = os.path.join('data', 'transcriptions')
    ensure_directory_exists(transcriptions_dir)

    transcription_files = [
        f for f in os.listdir(transcriptions_dir)
        if os.path.isfile(os.path.join(transcriptions_dir, f)) and f.endswith('.txt')
    ]

    if not transcription_files:
        cprint("Nenhuma transcrição encontrada na pasta 'transcriptions'.", "red", attrs=["bold"])
        return

    cprint(f"\n📝 Total de transcrições para processar: {len(transcription_files)}", "cyan")

    # Aviso especial para framework
    if prompt_type == "framework":
        cprint("\n⚠️  MODO FRAMEWORK ATIVADO", "yellow", attrs=["bold"])
        cprint("Este modo processa cada transcrição em 7 dimensões + síntese", "yellow")
        cprint("Tempo estimado: ~5-10 minutos por transcrição", "yellow")
        confirm = input(colored("\nDeseja continuar? (s/n): ", "magenta", attrs=["bold"])).strip().lower()
        if confirm != 's':
            cprint("Processamento cancelado.", "red")
            return

    for idx, transcription_file in enumerate(transcription_files, 1):
        # Pega o caminho completo do arquivo
        file_path = os.path.join(transcriptions_dir, transcription_file)

        cprint(f"\n[{idx}/{len(transcription_files)}] Processando: {transcription_file}", "yellow")
        try:
            if prompt_type == "framework":
                # Usa processador especial de framework
                from core.framework_processor import process_transcription_framework
                output_path = process_transcription_framework(file_path, output_language)
                cprint(f"✅ Framework completo gerado: {output_path}", "green", attrs=["bold"])
            else:
                # Usa processador normal (chunks)
                process_transcription(file_path, prompt_type, output_language)
                cprint(f"✅ Processamento concluído", "green")
        except Exception as e:
            cprint(f"❌ Erro ao processar: {e}", "red")
            import traceback
            traceback.print_exc()


def main():
    cprint("Bem-vindo ao Processador de Transcrições do YouTube!", "green", attrs=["bold"])

    # Verifica se há tarefa incompleta
    if progress_manager.has_incomplete_task():
        summary = progress_manager.get_progress_summary()
        cprint("\n⚠️  TAREFA INCOMPLETA DETECTADA!", "yellow", attrs=["bold"])
        cprint(f"Tipo: {summary['source_type'].upper()}", "cyan")
        cprint(f"Fonte: {summary['source_id']}", "cyan")
        cprint(f"Idiomas preferidos: {summary['language']}", "cyan")
        cprint(f"Progresso: {summary['current_index']}/{summary['total_videos']} vídeos ({summary['percentage']:.1f}%)", "cyan")
        cprint(f"Última atualização: {summary['last_update']}", "cyan")

        print("\n[1] Continuar de onde parou")
        print("[2] Começar uma nova tarefa (apaga o progresso anterior)")

        resume_choice = input(colored("\nDigite sua escolha (1 ou 2): ", "magenta", attrs=["bold"])).strip()

        if resume_choice == '1':
            # Retoma a tarefa
            progress = progress_manager.get_progress()
            download_transcriptions(
                progress["source_type"],
                progress["source_id"],
                progress["language"],
                progress.get("prompt_type") or "copywriting",
                progress.get("output_language") or "pt",
                resume=True
            )
            return
        elif resume_choice == '2':
            # Limpa o progresso e continua
            progress_manager.clear_progress()
            cprint("✓ Progresso anterior apagado.", "green")
        else:
            cprint("Escolha inválida. Por favor, tente novamente.", "red", attrs=["bold"])
            main()
            return

    # Nova tarefa - Seleção de configurações
    cprint("\n=== CONFIGURAÇÃO DO PROCESSAMENTO ===", "cyan", attrs=["bold"])

    # 1. Tipo de prompt
    cprint("\n📝 Escolha o tipo de análise:", "blue")
    print("[1] FAQ - Extração de conhecimento estruturado")
    print("[2] Copywriting - Frameworks de vendas high ticket")
    print("[3] Framework Completo - Extração profunda em 7 dimensões (RECOMENDADO)")
    prompt_choice = input(colored("Digite sua escolha (1, 2 ou 3): ", "magenta", attrs=["bold"])).strip()

    if prompt_choice == '1':
        prompt_type = "faq"
    elif prompt_choice == '2':
        prompt_type = "copywriting"
    elif prompt_choice == '3':
        prompt_type = "framework"
    else:
        cprint("Escolha inválida. Usando 'framework' como padrão.", "yellow")
        prompt_type = "framework"

    # 2. Idioma de saída
    cprint("\n🌍 Escolha o idioma de saída da IA:", "blue")
    print("[1] Português (pt)")
    print("[2] Inglês (en)")
    output_lang_choice = input(colored("Digite sua escolha (1 ou 2): ", "magenta", attrs=["bold"])).strip()

    if output_lang_choice == '1':
        output_language = "pt"
    elif output_lang_choice == '2':
        output_language = "en"
    else:
        cprint("Escolha inválida. Usando 'pt' como padrão.", "yellow")
        output_language = "pt"

    # 3. Idiomas preferidos para legendas
    cprint("\n📺 Idiomas preferidos para legendas (em ordem de prioridade):", "blue")
    print("Exemplos: 'pt,en' ou 'en,pt' ou 'pt' ou deixe vazio para qualquer idioma")
    lang_input = input(colored("Digite os códigos separados por vírgula: ", "magenta", attrs=["bold"])).strip()

    if lang_input:
        preferred_languages = [lang.strip() for lang in lang_input.split(',')]
    else:
        preferred_languages = None  # Aceita qualquer idioma disponível

    cprint(f"\n✓ Configurações salvas:", "green")
    cprint(f"  - Tipo de análise: {prompt_type.upper()}", "white")
    cprint(f"  - Idioma de saída: {output_language.upper()}", "white")
    cprint(f"  - Idiomas de legenda: {preferred_languages or 'Qualquer disponível'}", "white")

    # 4. Fonte dos vídeos
    cprint("\n🎬 Escolha a fonte dos vídeos:", "blue")
    print("[1] Playlist do YouTube")
    print("[2] Canal do YouTube")

    choice = input(colored("Digite sua escolha (1 ou 2): ", "magenta", attrs=["bold"])).strip()

    if choice == '1':
        playlist_url = input(colored("Digite a URL da playlist do YouTube: ", "magenta", attrs=["bold"])).strip()
        download_transcriptions("playlist", playlist_url, preferred_languages, prompt_type, output_language)
    elif choice == '2':
        channel_name = input(colored("Digite o nome do canal do YouTube: ", "magenta", attrs=["bold"])).strip()
        channel_id = get_channel_id_by_name(channel_name)
        if channel_id:
            download_transcriptions("canal", channel_id, preferred_languages, prompt_type, output_language)
        else:
            cprint("Erro: Canal não encontrado.", "red", attrs=["bold"])
    else:
        cprint("Escolha inválida. Por favor, tente novamente.", "red", attrs=["bold"])
        main()
        return

if __name__ == "__main__":
    main()