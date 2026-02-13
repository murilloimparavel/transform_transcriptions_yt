import os
import json
import time
from datetime import datetime
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


def process_multiple_videos(video_urls, preferred_languages=None, prompt_type="copywriting", output_language="pt"):
    """
    Processa múltiplos vídeos sequencialmente.

    Args:
        video_urls: Lista de URLs dos vídeos do YouTube
        preferred_languages: Lista de idiomas preferidos para legendas
        prompt_type: 'faq', 'copywriting', 'framework' ou 'agent_builder'
        output_language: Idioma do output ('pt' ou 'en')
    """
    total_videos = len(video_urls)
    cprint("\n" + "="*60, "cyan")
    cprint(f"🎬 PROCESSAMENTO DE {total_videos} VÍDEOS", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")

    # Estatísticas
    stats = {
        "total": total_videos,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "failed_videos": []
    }

    # Aviso especial para modos multi-stage com múltiplos vídeos
    if prompt_type in ["framework", "agent_builder"]:
        mode_name = "FRAMEWORK" if prompt_type == "framework" else "AGENT BUILDER"
        mode_desc = "7 dimensões + síntese" if prompt_type == "framework" else "7 blocos de conhecimento para agente IA"
        estimated_time = total_videos * 7  # ~7 minutos por vídeo
        cprint(f"\n⚠️  MODO {mode_name} ATIVADO", "yellow", attrs=["bold"])
        cprint(f"Este modo processa cada transcrição em {mode_desc}", "yellow")
        cprint(f"Tempo estimado: ~{estimated_time} minutos para {total_videos} vídeo(s)", "yellow")
        confirm = input(colored(f"\nDeseja processar {total_videos} vídeo(s) no modo {mode_name}? (s/n): ", "magenta", attrs=["bold"])).strip().lower()
        if confirm != 's':
            cprint("Processamento cancelado.", "red")
            return
    
    # Processa cada vídeo
    for idx, video_url in enumerate(video_urls, 1):
        cprint(f"\n{'='*60}", "cyan")
        cprint(f"[{idx}/{total_videos}] Processando vídeo {idx}", "cyan", attrs=["bold"])
        cprint(f"{'='*60}", "cyan")
        
        try:
            success = process_single_video(
                video_url, 
                preferred_languages, 
                prompt_type, 
                output_language,
                show_header=False,  # Não mostra header para cada vídeo
                video_number=f"{idx}/{total_videos}"  # Passa número do vídeo
            )
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                stats["failed_videos"].append({
                    "url": video_url,
                    "index": idx
                })
                
        except KeyboardInterrupt:
            cprint("\n\n⚠️  Processamento interrompido pelo usuário!", "yellow", attrs=["bold"])
            cprint(f"Processados {idx-1}/{total_videos} vídeos antes da interrupção.", "cyan")
            break
        except Exception as e:
            if "429" in str(e):
                cprint("⚠️ Cota estourada (429). Aguardando 60 segundos...", "red", attrs=["bold"])
                time.sleep(60)

            cprint(f"\n❌ Erro ao processar vídeo {idx}: {e}", "red", attrs=["bold"])
            stats["failed"] += 1
            stats["failed_videos"].append({
                "url": video_url,
                "index": idx,
                "error": str(e)
            })
        
        # Pausa entre vídeos (exceto no último)
        if idx < total_videos:
            cprint(f"\n⏳ Aguardando 30 segundos antes do próximo vídeo para evitar Rate Limit...", "blue")
            time.sleep(30)
    
    # Mostra estatísticas finais
    cprint("\n" + "="*60, "cyan")
    cprint("📊 ESTATÍSTICAS FINAIS", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")
    cprint(f"Total de vídeos: {stats['total']}", "white")
    cprint(f"✅ Sucessos: {stats['success']}", "green")
    cprint(f"❌ Falharam: {stats['failed']}", "red" if stats['failed'] > 0 else "white")
    
    if stats['failed_videos']:
        cprint(f"\n📋 Vídeos que falharam ({len(stats['failed_videos'])}):", "yellow", attrs=["bold"])
        for failed in stats['failed_videos']:
            cprint(f"  [{failed['index']}] {failed['url'][:60]}...", "yellow")
            if 'error' in failed:
                cprint(f"      Erro: {failed['error']}", "red")

    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    cprint(f"\n✨ Taxa de sucesso: {success_rate:.1f}%", "green", attrs=["bold"])
    cprint("="*60 + "\n", "cyan")

    # Consolidação automática para Agent Builder
    if prompt_type == "agent_builder" and stats['success'] > 0:
        cprint("\n🔗 Iniciando consolidação automática do Agent Builder...", "cyan", attrs=["bold"])
        try:
            from core.agent_consolidator import consolidate_agent_builder_outputs

            # Pergunta nome do projeto
            project_name = input(colored("\nDigite um nome para o projeto (ou Enter para usar timestamp): ", "magenta", attrs=["bold"])).strip()
            if not project_name:
                project_name = f"projeto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            output_dir = consolidate_agent_builder_outputs(
                source_dir=os.path.join('data', 'processed'),
                project_name=project_name,
                output_language=output_language
            )

            if output_dir:
                cprint(f"\n🎉 Consolidação concluída!", "green", attrs=["bold"])
                cprint(f"📁 Arquivos organizados em: {output_dir}", "white")
                cprint("\n📂 Estrutura de pastas:", "cyan")
                cprint("   ├── mega_planilha/     → Planilha Excel consolidada", "white")
                cprint("   ├── system_prompt/     → System Prompt para o agente", "white")
                cprint("   ├── json/              → JSONs originais de cada vídeo", "white")
                cprint("   └── txt/               → TXTs originais de cada vídeo", "white")
        except Exception as e:
            cprint(f"\n⚠️  Erro na consolidação: {e}", "yellow", attrs=["bold"])
            cprint("   Os arquivos individuais foram gerados com sucesso.", "white")
            import traceback
            traceback.print_exc()


def process_single_video(video_url, preferred_languages=None, prompt_type="copywriting", output_language="pt", show_header=True, video_number=None):
    """
    Processa um único vídeo: baixa transcrição e processa imediatamente.

    Args:
        video_url: URL do vídeo do YouTube
        preferred_languages: Lista de idiomas preferidos para legendas
        prompt_type: 'faq', 'copywriting', 'framework' ou 'agent_builder'
        output_language: Idioma do output ('pt' ou 'en')
        show_header: Se deve mostrar o cabeçalho (padrão: True)
        video_number: Número do vídeo no formato "X/Y" (opcional)

    Returns:
        bool: True se processado com sucesso, False caso contrário
    """
    if show_header:
        cprint("\n" + "="*60, "cyan")
        cprint("🎬 PROCESSAMENTO DE VÍDEO ÚNICO", "cyan", attrs=["bold"])
        cprint("="*60, "cyan")
    
    from core.transcription import get_video_id
    video_id = get_video_id(video_url)
    
    if video_number:
        cprint(f"\n📹 Vídeo {video_number} - ID: {video_id}", "blue")
    else:
        cprint(f"\n📹 Vídeo ID: {video_id}", "blue")
    cprint(f"🔗 URL: {video_url}", "blue")
    
    # 1. Baixa a transcrição
    cprint("\n📥 Baixando transcrição...", "yellow", attrs=["bold"])
    
    # Converte idiomas para lista se necessário
    if preferred_languages is None:
        preferred_langs = None
    elif isinstance(preferred_languages, list):
        preferred_langs = preferred_languages
    else:
        preferred_langs = [preferred_languages]
    
    transcription_path = download_transcription(video_url, preferred_langs, max_retries=3)
    
    if not transcription_path:
        cprint("❌ Não foi possível baixar a transcrição do vídeo.", "red", attrs=["bold"])
        cprint("   Verifique se o vídeo possui legendas habilitadas.", "yellow")
        return False
    
    used_lang = os.path.splitext(transcription_path)[0].split("_")[-1]
    cprint(f"✅ Transcrição baixada com sucesso! [{used_lang}]", "green", attrs=["bold"])
    cprint(f"   Arquivo: {transcription_path}", "white")
    
    # 2. Processa a transcrição
    cprint(f"\n🤖 Processando transcrição com: {prompt_type.upper()}", "cyan", attrs=["bold"])
    cprint(f"🌍 Idioma de saída: {output_language.upper()}", "cyan")

    # Aviso especial para modos multi-stage (apenas se for vídeo único)
    if prompt_type in ["framework", "agent_builder"] and not video_number:
        mode_name = "FRAMEWORK" if prompt_type == "framework" else "AGENT BUILDER"
        mode_desc = "7 dimensões + síntese" if prompt_type == "framework" else "7 blocos de conhecimento para agente IA"
        cprint(f"\n⚠️  MODO {mode_name} ATIVADO", "yellow", attrs=["bold"])
        cprint(f"Este modo processa a transcrição em {mode_desc}", "yellow")
        cprint("Tempo estimado: ~5-10 minutos", "yellow")
        confirm = input(colored("\nDeseja continuar? (s/n): ", "magenta", attrs=["bold"])).strip().lower()
        if confirm != 's':
            cprint("Processamento cancelado.", "red")
            return False

    try:
        if prompt_type == "framework":
            # Usa processador especial de framework
            from core.framework_processor import process_transcription_framework
            output_path = process_transcription_framework(transcription_path, output_language)
            cprint(f"\n✅ Framework completo gerado!", "green", attrs=["bold"])
            cprint(f"   Arquivo: {output_path}", "white")
        elif prompt_type == "agent_builder":
            # Usa processador especial de agent builder
            from core.agent_builder_processor import process_transcription_agent_builder
            output_path = process_transcription_agent_builder(transcription_path, output_language)
            cprint(f"\n✅ Base de conhecimento para agente gerada!", "green", attrs=["bold"])
            cprint(f"   Arquivo TXT: {output_path}", "white")
            cprint(f"   Arquivo JSON: {output_path.replace('.txt', '.json')}", "white")
        else:
            # Usa processador normal (chunks)
            process_transcription(transcription_path, prompt_type, output_language)
            cprint(f"\n✅ Processamento concluído!", "green", attrs=["bold"])

            # Mostra onde o arquivo foi salvo
            output_dir = os.path.join('data', 'processed')
            base_name = os.path.basename(transcription_path).replace('.txt', '')
            output_file = os.path.join(output_dir, f"{base_name}_{prompt_type}_{output_language}_processed.txt")
            if os.path.exists(output_file):
                cprint(f"   Arquivo: {output_file}", "white")
        
        if not video_number:  # Só mostra mensagem final se for vídeo único
            cprint("\n" + "="*60, "green")
            cprint("🎉 PROCESSAMENTO CONCLUÍDO COM SUCESSO!", "green", attrs=["bold"])
            cprint("="*60, "green")
        
        return True
        
    except Exception as e:
        cprint(f"\n❌ Erro ao processar transcrição: {e}", "red", attrs=["bold"])
        import traceback
        traceback.print_exc()
        return False


def process_documents(prompt_type="faq", output_language="pt"):
    """
    Processa documentos de diferentes fontes: sites, PDFs e Word.
    
    Args:
        prompt_type: 'faq' ou 'framework' (copywriting não faz sentido para documentos)
        output_language: Idioma do output ('pt' ou 'en')
    """
    cprint("\n" + "="*60, "cyan")
    cprint("📄 PROCESSAMENTO DE DOCUMENTOS", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")
    
    # Valida tipo de prompt
    if prompt_type == "copywriting":
        cprint("⚠️  Copywriting não é recomendado para documentos.", "yellow")
        cprint("   Alterando para FAQ...", "yellow")
        prompt_type = "faq"
    
    cprint("\n📋 Formatos suportados:", "blue")
    print("  • URL de site (https://exemplo.com)")
    print("  • Arquivo PDF (.pdf)")
    print("  • Documento Word (.docx)")
    print("  • Arquivo de texto (.txt)")
    print("  • Arquivo Markdown (.md)")
    print("  • Planilha Excel (.xlsx, .xls)")
    print("  • Arquivo CSV (.csv)")
    
    cprint("\n💡 Dica: Você pode fornecer múltiplas fontes separadas por vírgula", "white")
    cprint("   Exemplo: https://site.com, documento.pdf, arquivo.docx, texto.txt, planilha.xlsx, dados.csv", "white")
    
    sources_input = input(colored("\nDigite a(s) fonte(s) (URL ou caminho do arquivo): ", "magenta", attrs=["bold"])).strip()
    
    if not sources_input:
        cprint("❌ Nenhuma fonte fornecida.", "red", attrs=["bold"])
        return
    
    # Separa as fontes
    sources = [s.strip() for s in sources_input.split(',') if s.strip()]
    
    if not sources:
        cprint("❌ Nenhuma fonte válida encontrada.", "red", attrs=["bold"])
        return
    
    # Limita a 10 fontes
    if len(sources) > 10:
        cprint(f"⚠️  Você forneceu {len(sources)} fontes. Limitando a 10.", "yellow")
        sources = sources[:10]
    
    # Pergunta sobre consolidação (apenas para FAQ e múltiplas fontes)
    consolidate_faqs = False
    if prompt_type == "faq" and len(sources) > 1:
        cprint("\n📊 Opções de geração de FAQ:", "blue")
        print("[1] Gerar planilha separada para cada fonte")
        print("[2] Consolidar todos os FAQs em uma única planilha")
        consolidate_choice = input(colored("\nDigite sua escolha (1 ou 2): ", "magenta", attrs=["bold"])).strip()
        
        if consolidate_choice == '2':
            consolidate_faqs = True
            cprint("✅ Todos os FAQs serão consolidados em uma única planilha", "green")
        else:
            cprint("✅ Cada FAQ será gerado em uma planilha separada", "green")
    
    # Processa cada fonte
    stats = {
        "total": len(sources),
        "success": 0,
        "failed": 0,
        "failed_sources": []
    }
    
    # Lista para armazenar FAQs se for consolidar
    all_faqs = [] if consolidate_faqs else None
    source_names = [] if consolidate_faqs else None
    
    for idx, source in enumerate(sources, 1):
        cprint(f"\n{'='*60}", "cyan")
        cprint(f"[{idx}/{len(sources)}] Processando fonte {idx}", "cyan", attrs=["bold"])
        cprint(f"{'='*60}", "cyan")
        
        try:
            result = process_single_document(
                source, 
                prompt_type, 
                output_language, 
                idx, 
                len(sources),
                consolidate=consolidate_faqs
            )
            
            if isinstance(result, dict) and result.get("success"):
                stats["success"] += 1
                # Se consolidar, armazena FAQ
                if consolidate_faqs and "faq_text" in result:
                    all_faqs.append(result["faq_text"])
                    source_names.append(result.get("source_name", f"Fonte {idx}"))
            elif isinstance(result, bool) and result:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                stats["failed_sources"].append({"source": source, "index": idx})
        except KeyboardInterrupt:
            cprint("\n\n⚠️  Processamento interrompido pelo usuário!", "yellow", attrs=["bold"])
            break
        except Exception as e:
            cprint(f"\n❌ Erro ao processar fonte {idx}: {e}", "red", attrs=["bold"])
            stats["failed"] += 1
            stats["failed_sources"].append({"source": source, "index": idx, "error": str(e)})
        
        # Pausa entre fontes
        if idx < len(sources):
            cprint(f"\n⏳ Aguardando 3 segundos antes da próxima fonte...", "blue")
            time.sleep(3)
    
    # Estatísticas finais
    cprint("\n" + "="*60, "cyan")
    cprint("📊 ESTATÍSTICAS FINAIS", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")
    cprint(f"Total de fontes: {stats['total']}", "white")
    cprint(f"✅ Sucessos: {stats['success']}", "green")
    cprint(f"❌ Falharam: {stats['failed']}", "red" if stats['failed'] > 0 else "white")
    
    if stats['failed_sources']:
        cprint(f"\n📋 Fontes que falharam:", "yellow", attrs=["bold"])
        for failed in stats['failed_sources']:
            source_display = failed['source'][:60] + "..." if len(failed['source']) > 60 else failed['source']
            cprint(f"  [{failed['index']}] {source_display}", "yellow")
            if 'error' in failed:
                cprint(f"      Erro: {failed['error']}", "red")
    
    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
    cprint(f"\n✨ Taxa de sucesso: {success_rate:.1f}%", "green", attrs=["bold"])
    cprint("="*60, "cyan")
    
    # Se consolidar FAQs, gera planilha única
    if consolidate_faqs and all_faqs and len(all_faqs) > 0:
        cprint("\n📊 Consolidando todos os FAQs em uma única planilha...", "cyan", attrs=["bold"])
        try:
            from core.faq_to_excel import create_consolidated_faq_excel
            
            output_dir = os.path.join('data', 'processed', 'documents')
            consolidated_path = os.path.join(output_dir, f"FAQ_Consolidado_{output_language}.xlsx")
            
            total_items = create_consolidated_faq_excel(all_faqs, source_names, consolidated_path, output_language)
            
            cprint(f"✅ Planilha consolidada gerada com sucesso!", "green", attrs=["bold"])
            cprint(f"   Total de itens FAQ: {total_items}", "white")
            cprint(f"   Arquivo: {consolidated_path}", "white")
        except Exception as e:
            cprint(f"⚠️  Erro ao consolidar FAQs: {e}", "yellow", attrs=["bold"])
            cprint("   Os FAQs individuais foram gerados com sucesso.", "white")
            import traceback
            traceback.print_exc()
    
    cprint("\n", "cyan")


def process_single_document(source, prompt_type, output_language, doc_number=None, total_docs=None, consolidate=False):
    """
    Processa um único documento (site, PDF ou Word).

    Args:
        source: URL ou caminho do arquivo
        prompt_type: 'faq', 'framework' ou 'agent_builder'
        output_language: Idioma do output
        doc_number: Número do documento (opcional)
        total_docs: Total de documentos (opcional)
        consolidate: Se True, não gera Excel individual (apenas retorna FAQ)

    Returns:
        bool ou dict: True se processado com sucesso, ou dict com FAQ se consolidate=True
    """
    from core.document_extractor import extract_text_from_source
    from core.processing import process_transcription
    from core.framework_processor import process_transcription_framework
    from core.agent_builder_processor import process_transcription_agent_builder
    from core.faq_to_excel import create_faq_excel
    
    try:
        # Extrai texto da fonte
        cprint(f"\n📥 Extraindo texto da fonte...", "yellow", attrs=["bold"])
        text, source_type = extract_text_from_source(source)
        
        # Cria nome base para arquivos
        if source_type == "url":
            from urllib.parse import urlparse
            parsed = urlparse(source)
            base_name = parsed.netloc.replace('.', '_').replace('www_', '')[:30]
        else:
            base_name = os.path.splitext(os.path.basename(source))[0]
        
        # Salva texto extraído temporariamente
        temp_dir = os.path.join('data', 'transcriptions', 'documents')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"{base_name}_extracted.txt")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        cprint(f"✅ Texto extraído e salvo: {len(text)} caracteres", "green", attrs=["bold"])
        
        # Processa o texto
        cprint(f"\n🤖 Processando com: {prompt_type.upper()}", "cyan", attrs=["bold"])
        cprint(f"🌍 Idioma de saída: {output_language.upper()}", "cyan")
        
        output_dir = os.path.join('data', 'processed', 'documents')
        os.makedirs(output_dir, exist_ok=True)
        
        if prompt_type == "framework":
            # Processa com framework
            output_path = os.path.join(output_dir, f"{base_name}_framework_{output_language}.txt")
            process_transcription_framework(temp_file, output_language)

            # Move arquivo gerado para o local correto
            framework_output = os.path.join('data', 'processed', f"{base_name}_extracted_framework_{output_language}.txt")
            if os.path.exists(framework_output):
                import shutil
                shutil.move(framework_output, output_path)

            cprint(f"\n✅ Framework completo gerado!", "green", attrs=["bold"])
            cprint(f"   Arquivo: {output_path}", "white")

        elif prompt_type == "agent_builder":
            # Processa com agent builder
            output_path = os.path.join(output_dir, f"{base_name}_agent_builder_{output_language}.txt")
            process_transcription_agent_builder(temp_file, output_language)

            # Move arquivo gerado para o local correto
            agent_output = os.path.join('data', 'processed', f"{base_name}_extracted_agent_builder_{output_language}.txt")
            if os.path.exists(agent_output):
                import shutil
                shutil.move(agent_output, output_path)
                # Move também o JSON
                agent_json = agent_output.replace('.txt', '.json')
                if os.path.exists(agent_json):
                    shutil.move(agent_json, output_path.replace('.txt', '.json'))

            cprint(f"\n✅ Base de conhecimento para agente gerada!", "green", attrs=["bold"])
            cprint(f"   Arquivo TXT: {output_path}", "white")
            cprint(f"   Arquivo JSON: {output_path.replace('.txt', '.json')}", "white")

        else:  # FAQ
            # Processa com FAQ
            process_transcription(temp_file, prompt_type, output_language)
            
            # Lê resultado processado
            processed_file = os.path.join('data', 'processed', f"{base_name}_extracted_{prompt_type}_{output_language}_processed.txt")
            
            if os.path.exists(processed_file):
                with open(processed_file, 'r', encoding='utf-8') as f:
                    faq_text = f.read()
                
                # Se consolidar, retorna FAQ sem gerar Excel individual
                if consolidate:
                    cprint(f"\n✅ FAQ processado! (será consolidado)", "green", attrs=["bold"])
                    return {
                        "success": True,
                        "faq_text": faq_text,
                        "source_name": base_name
                    }
                
                # Gera Excel individual
                excel_path = os.path.join(output_dir, f"{base_name}_FAQ_{output_language}.xlsx")
                num_items = create_faq_excel(faq_text, excel_path, base_name)
                
                # Move arquivo TXT também
                txt_path = os.path.join(output_dir, f"{base_name}_FAQ_{output_language}.txt")
                import shutil
                shutil.move(processed_file, txt_path)
                
                cprint(f"\n✅ FAQ processado e Excel gerado!", "green", attrs=["bold"])
                cprint(f"   Total de itens FAQ: {num_items}", "white")
                cprint(f"   Arquivo Excel: {excel_path}", "white")
                cprint(f"   Arquivo TXT: {txt_path}", "white")
            else:
                cprint(f"⚠️  Arquivo processado não encontrado: {processed_file}", "yellow")
                return False
        
        return True
        
    except FileNotFoundError as e:
        cprint(f"❌ Arquivo não encontrado: {e}", "red", attrs=["bold"])
        return False
    except ValueError as e:
        cprint(f"❌ Erro de validação: {e}", "red", attrs=["bold"])
        return False
    except Exception as e:
        cprint(f"❌ Erro ao processar documento: {e}", "red", attrs=["bold"])
        import traceback
        traceback.print_exc()
        return False


def process_all_transcriptions(prompt_type="copywriting", output_language="pt"):
    """
    Processa todos os arquivos de transcrição presentes na pasta 'data/transcriptions'.

    Args:
        prompt_type: 'faq', 'copywriting', 'framework' ou 'agent_builder'
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

    # Aviso especial para modos multi-stage
    if prompt_type in ["framework", "agent_builder"]:
        mode_name = "FRAMEWORK" if prompt_type == "framework" else "AGENT BUILDER"
        mode_desc = "7 dimensões + síntese" if prompt_type == "framework" else "7 blocos de conhecimento para agente IA"
        cprint(f"\n⚠️  MODO {mode_name} ATIVADO", "yellow", attrs=["bold"])
        cprint(f"Este modo processa cada transcrição em {mode_desc}", "yellow")
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
            elif prompt_type == "agent_builder":
                # Usa processador especial de agent builder
                from core.agent_builder_processor import process_transcription_agent_builder
                output_path = process_transcription_agent_builder(file_path, output_language)
                cprint(f"✅ Base de conhecimento gerada: {output_path}", "green", attrs=["bold"])
            else:
                # Usa processador normal (chunks)
                process_transcription(file_path, prompt_type, output_language)
                cprint(f"✅ Processamento concluído", "green")
            
            # ESPERE 30 SEGUNDOS entre cada vídeo para não estourar a cota gratuita
            if idx < len(transcription_files):
                cprint(f"⏳ Aguardando 30 segundos para evitar Rate Limit...", "blue")
                time.sleep(30)

        except Exception as e:
            if "429" in str(e):
                cprint("⚠️ Cota estourada (429). Aguardando 60 segundos...", "red", attrs=["bold"])
                time.sleep(60)
            else:
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
    print("[3] Framework Completo - Extração profunda em 7 dimensões")
    print("[4] Agent Builder - Base de conhecimento para treinar agentes IA (RECOMENDADO)")
    prompt_choice = input(colored("Digite sua escolha (1, 2, 3 ou 4): ", "magenta", attrs=["bold"])).strip()

    if prompt_choice == '1':
        prompt_type = "faq"
    elif prompt_choice == '2':
        prompt_type = "copywriting"
    elif prompt_choice == '3':
        prompt_type = "framework"
    elif prompt_choice == '4':
        prompt_type = "agent_builder"
    else:
        cprint("Escolha inválida. Usando 'agent_builder' como padrão.", "yellow")
        prompt_type = "agent_builder"

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

    # 4. Fonte dos vídeos/documentos
    cprint("\n🎬 Escolha a fonte de conteúdo:", "blue")
    print("[1] Playlist do YouTube")
    print("[2] Canal do YouTube")
    print("[3] Vídeo(s) do YouTube")
    print("[4] Documentos (Site, PDF, Word)")
    print("[5] Consolidar Agent Builder (arquivos já processados)")

    choice = input(colored("Digite sua escolha (1, 2, 3, 4 ou 5): ", "magenta", attrs=["bold"])).strip()

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
    elif choice == '3':
        video_input = input(colored("Digite a URL do(s) vídeo(s) do YouTube (separados por vírgula, máximo 10): ", "magenta", attrs=["bold"])).strip()
        # Validação básica
        if not video_input:
            cprint("❌ Nenhuma URL fornecida. Por favor, forneça pelo menos uma URL válida.", "red", attrs=["bold"])
            main()
            return
        
        # Separa as URLs por vírgula
        video_urls = [url.strip() for url in video_input.split(',') if url.strip()]
        
        if not video_urls:
            cprint("❌ Nenhuma URL válida encontrada.", "red", attrs=["bold"])
            main()
            return
        
        # Limita a 10 vídeos
        if len(video_urls) > 10:
            cprint(f"⚠️  Você forneceu {len(video_urls)} vídeos. Limitando a 10 vídeos.", "yellow")
            video_urls = video_urls[:10]
        
        # Valida URLs
        valid_urls = []
        for url in video_urls:
            if "youtube.com" not in url and "youtu.be" not in url:
                cprint(f"⚠️  URL ignorada (não parece ser do YouTube): {url[:50]}...", "yellow")
            else:
                valid_urls.append(url)
        
        if not valid_urls:
            cprint("❌ Nenhuma URL válida do YouTube encontrada.", "red", attrs=["bold"])
            main()
            return
        
        # Processa múltiplos vídeos
        if len(valid_urls) == 1:
            process_single_video(valid_urls[0], preferred_languages, prompt_type, output_language)
        else:
            process_multiple_videos(valid_urls, preferred_languages, prompt_type, output_language)
    elif choice == '4':
        process_documents(prompt_type, output_language)
    elif choice == '5':
        consolidate_existing_agent_builder(output_language)
    else:
        cprint("Escolha inválida. Por favor, tente novamente.", "red", attrs=["bold"])
        main()
        return


def consolidate_existing_agent_builder(output_language="pt"):
    """
    Consolida arquivos Agent Builder já processados anteriormente.
    """
    from core.agent_consolidator import consolidate_agent_builder_outputs

    cprint("\n" + "="*60, "cyan")
    cprint("🔗 CONSOLIDAÇÃO DE AGENT BUILDER", "cyan", attrs=["bold"])
    cprint("="*60, "cyan")

    # Verifica se existem arquivos
    source_dir = os.path.join('data', 'processed')
    if not os.path.exists(source_dir):
        cprint("❌ Diretório data/processed não encontrado.", "red", attrs=["bold"])
        return

    # Conta arquivos Agent Builder
    agent_files = [f for f in os.listdir(source_dir) if 'agent_builder' in f and f.endswith('.json')]

    if not agent_files:
        cprint("❌ Nenhum arquivo Agent Builder encontrado em data/processed/", "red", attrs=["bold"])
        cprint("   Execute primeiro o processamento de vídeos com a opção Agent Builder.", "yellow")
        return

    cprint(f"\n📁 Encontrados {len(agent_files)} arquivos Agent Builder para consolidar:", "blue")
    for f in agent_files[:10]:  # Mostra no máximo 10
        cprint(f"   • {f}", "white")
    if len(agent_files) > 10:
        cprint(f"   ... e mais {len(agent_files) - 10} arquivos", "white")

    # Nome do projeto
    project_name = input(colored("\nDigite um nome para o projeto: ", "magenta", attrs=["bold"])).strip()
    if not project_name:
        project_name = f"projeto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Executa consolidação
    try:
        output_dir = consolidate_agent_builder_outputs(
            source_dir=source_dir,
            project_name=project_name,
            output_language=output_language
        )

        if output_dir:
            cprint(f"\n🎉 Consolidação concluída com sucesso!", "green", attrs=["bold"])
            cprint(f"📁 Arquivos organizados em: {output_dir}", "white")
            cprint("\n📂 Estrutura de pastas criada:", "cyan")
            cprint("   ├── mega_planilha/     → Planilha Excel com todo o conhecimento", "white")
            cprint("   ├── system_prompt/     → System Prompt consolidado para o agente", "white")
            cprint("   ├── json/              → JSONs originais de cada vídeo", "white")
            cprint("   └── txt/               → TXTs originais de cada vídeo", "white")
            cprint("\n💡 Próximos passos:", "blue")
            cprint("   1. Use a mega_planilha para criar embeddings (RAG)", "white")
            cprint("   2. Use o system_prompt como base para seu agente", "white")
            cprint("   3. Os JSONs podem ser usados para integração programática", "white")
    except Exception as e:
        cprint(f"\n❌ Erro na consolidação: {e}", "red", attrs=["bold"])
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()