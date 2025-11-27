import os
import time
import logging
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

try:
    from .proxy_manager import get_proxy_manager
except ImportError:
    # Fallback se não conseguir importar
    def get_proxy_manager(*args, **kwargs):
        return None

# Configuração de logs
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Logger para arquivo (detalhado)
file_handler = logging.FileHandler(os.path.join(log_dir, "transcriptions.log"), encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Logger para console (simplificado - apenas WARNING e ERROR)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Só mostra WARNING e ERROR no console
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

logging.basicConfig(
    level=logging.INFO,  # Captura tudo
    handlers=[file_handler, console_handler]
)

def get_video_id(url):
    """Extrai o ID do vídeo da URL do YouTube."""
    parsed_url = urlparse(url)
    video_id = parse_qs(parsed_url.query).get('v')
    if video_id:
        return video_id[0]
    else:
        return parsed_url.path.split('/')[-1]

def get_available_transcripts(video_id):
    """
    Lista todas as transcrições disponíveis para um vídeo.

    Returns:
        list: Lista de códigos de idioma disponíveis, ou lista vazia se nenhum
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        return [t.language_code for t in transcript_list]
    except Exception:
        return []

def get_transcript_from_youtube(video_id, preferred_languages=None, proxies=None):
    """
    Tenta obter a transcrição do YouTube, priorizando idiomas preferidos.

    Args:
        video_id: ID do vídeo
        preferred_languages: Lista de idiomas preferidos em ordem de prioridade (ex: ['pt', 'en'])
                           Se None, pega qualquer legenda disponível
        proxies: Dict de proxies para requests (ex: {"http": "...", "https": "..."})

    Returns:
        tuple: (texto_da_transcrição, código_do_idioma)
    """
    try:
        # A biblioteca youtube-transcript-api usa requests internamente
        # Para usar proxy, precisamos configurar através de monkey patching
        if proxies:
            logging.info(f"[{video_id}] Usando proxy: {proxies.get('http', 'N/A')[:30]}...")
            # Configura proxies no módulo requests globalmente (temporário)
            import requests
            original_get = requests.get
            original_post = requests.post

            def patched_get(*args, **kwargs):
                kwargs['proxies'] = proxies
                return original_get(*args, **kwargs)

            def patched_post(*args, **kwargs):
                kwargs['proxies'] = proxies
                return original_post(*args, **kwargs)

            requests.get = patched_get
            requests.post = patched_post

        # Cria instância da API e lista as transcrições
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        transcript = None

        # Se especificou idiomas preferidos, tenta nessa ordem
        if preferred_languages:
            for lang in preferred_languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    logging.info(f"[{video_id}] Legenda encontrada no idioma preferido: {lang}")
                    break
                except NoTranscriptFound:
                    continue

        # Se não encontrou nos preferidos (ou não especificou), pega a primeira disponível
        if transcript is None:
            # Tenta pegar qualquer transcrição disponível
            try:
                # Primeiro tenta manual
                available = [t for t in transcript_list if not t.is_generated]
                if not available:
                    # Se não tiver manual, aceita gerada automaticamente
                    available = [t for t in transcript_list]

                if not available:
                    raise NoTranscriptFound(video_id, preferred_languages or [], None)

                transcript = available[0]
                logging.info(f"[{video_id}] Usando primeira legenda disponível: {transcript.language_code}")
            except Exception:
                raise NoTranscriptFound(video_id, preferred_languages or [], None)

        # Busca o conteúdo da transcrição
        data = transcript.fetch()
        lang = transcript.language_code

        # Formata o texto
        text = "\n".join([entry['text'] for entry in data])

        # Restaura requests se foi modificado
        if proxies:
            import requests
            requests.get = original_get
            requests.post = original_post

        return text, lang

    except Exception as e:
        # Restaura requests em caso de erro
        if proxies:
            import requests
            try:
                requests.get = original_get
                requests.post = original_post
            except:
                pass
        raise e

def get_transcript_from_kome(video_id):
    """Fallback para pegar transcrição usando API do kome.ai"""
    url = "https://kome.ai/api/transcript"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7,es;q=0.6",
        "content-type": "application/json",
        "origin": "https://kome.ai",
        "priority": "u=1, i",
        "referer": "https://kome.ai/tools/youtube-transcript-generator",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "cookie": "_ga=GA1.1.1976331997.1757256287; _ga_J58R10RFE6=GS2.1.s1757902272$o2$g1$t1757902285$j47$l0$h0;"
    }
    payload = {
        "video_id": f"https://www.youtube.com/watch?v={video_id}",
        "format": True
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()

    try:
        data = resp.json()
    except Exception:
        raise ValueError(f"Kome.ai não retornou JSON válido: {resp.status_code} {resp.text[:500]}")

    # ✅ trata os dois formatos possíveis: lista e dict
    if isinstance(data, dict) and "transcript" in data:
        return data["transcript"], "kome"
    elif isinstance(data, list) and data and "transcript" in data[0]:
        return data[0]["transcript"], "kome"
    else:
        raise ValueError(f"Resposta inesperada do Kome.ai: {data}")

def download_transcription(video_url, preferred_languages=None, max_retries=3):
    """
    Tenta baixar transcrição com limite de tentativas, auto-detectando idioma.

    Args:
        video_url: URL do vídeo do YouTube
        preferred_languages: Lista de idiomas preferidos (ex: ['pt', 'en'])
                           Se None, pega qualquer legenda disponível
        max_retries: Número máximo de tentativas (padrão: 3)

    Returns:
        Caminho do arquivo de transcrição ou None se não conseguir
    """
    use_proxies = os.environ.get("USE_PROXIES", "false").lower() == "true"
    video_id = get_video_id(video_url)
    output_dir = os.path.join("data", "transcriptions")
    os.makedirs(output_dir, exist_ok=True)

    # 🔎 verifica se já existe algum arquivo de transcrição desse vídeo
    existing_files = [
        f for f in os.listdir(output_dir)
        if f.startswith(video_id + "_") and f.endswith(".txt")
    ]
    if existing_files:
        file_path = os.path.join(output_dir, existing_files[0])
        logging.info(f"[{video_id}] Transcrição já existe -> {file_path} (pulando download)")
        return file_path  # 🚀 retorna direto, sem delay

    retry_count = 0
    youtube_api_failed_permanently = False

    # Inicializa proxy manager se habilitado
    proxy_manager = None
    current_proxy = None

    if use_proxies:
        proxy_manager = get_proxy_manager(use_proxies=True)
        
        # Lógica robusta de carregamento de proxies
        if not proxy_manager.proxies:
            logging.info(f"[{video_id}] Lista de proxies vazia. Tentando carregar BR...")
            proxy_manager.load_proxies("br")
            
        if not proxy_manager.proxies:
            logging.warning(f"[{video_id}] Proxies BR falharam. Tentando globais (Proxifly)...")
            proxy_manager.load_proxies("proxifly")
            
        if not proxy_manager.proxies:
            logging.warning(f"[{video_id}] Proxifly falhou. Tentando globais (ProxyScrape)...")
            proxy_manager.load_proxies("proxyscrape")
            
        if proxy_manager.proxies:
            # Pega o próximo da fila sem testar (teste será na prática)
            current_proxy = proxy_manager.get_next_proxy()
            if current_proxy:
                logging.info(f"[{video_id}] Usando proxy inicial: {current_proxy[:30]}...")
        else:
            logging.error(f"[{video_id}] FALHA CRÍTICA: Não foi possível carregar nenhum proxy de nenhuma fonte.")

    while retry_count < max_retries:
        transcript_text, source_lang, source = None, None, None

        # Tenta a API do YouTube, a menos que tenha falhado permanentemente
        if not youtube_api_failed_permanently:
            try:
                # Usa proxy se disponível
                proxies_dict = None
                if use_proxies and proxy_manager and current_proxy:
                    proxies_dict = proxy_manager.get_proxy_dict(current_proxy)

                transcript_text, source_lang = get_transcript_from_youtube(
                    video_id,
                    preferred_languages,
                    proxies=proxies_dict
                )
                source = "YouTubeTranscriptApi"
                logging.info(f"[{video_id}] Transcrição encontrada via YouTube ({source_lang})")
                
                # ✅ SE SUCESSO, SALVA O PROXY NA LISTA VIP
                if use_proxies and proxy_manager and current_proxy:
                    proxy_manager.mark_proxy_success(current_proxy)

            except Exception as e1:
                error_msg = str(e1)

                # Simplifica mensagem de erro para o log
                if "Could not retrieve a transcript" in error_msg:
                    if "Subtitles are disabled" in error_msg:
                        error_summary = "Legendas desabilitadas"
                        logging.warning(f"[{video_id}] {error_summary}")
                    elif "blocking requests" in error_msg:
                        # IP bloqueado - log apenas no arquivo (INFO)
                        logging.info(f"[{video_id}] IP bloqueado - rotacionando proxy...")
                    else:
                        error_summary = "Transcrição não disponível"
                        logging.warning(f"[{video_id}] {error_summary}")
                else:
                    logging.warning(f"[{video_id}] Falha YouTubeTranscriptApi: {str(e1)[:100]}")

                # Detecta bloqueio de IP e decide o que fazer
                if "blocking requests from your IP" in error_msg or "IPBlocked" in error_msg:
                    if use_proxies and proxy_manager:
                        # Marca o atual como ruim
                        proxy_manager.mark_proxy_failed(current_proxy)
                        
                        # Pega o próximo imediatamente
                        current_proxy = proxy_manager.get_next_proxy()

                        if current_proxy:
                            # Log apenas no arquivo (INFO não aparece no console)
                            logging.info(f"[{video_id}] 🔄 Proxy bloqueado - rotacionando...")
                            continue  # Tenta de novo com novo proxy
                        else:
                            logging.warning(f"[{video_id}] ⚠️  Todos os proxies falharam - usando Kome.ai")
                            youtube_api_failed_permanently = True
                    else:
                        # Não está usando proxies ou o manager falhou
                        logging.warning(f"[{video_id}] ⚠️  IP BLOQUEADO pelo YouTube - mudando para Kome.ai")
                        if not use_proxies:
                            logging.warning(f"[{video_id}] 💡 Dica: Ative proxies com USE_PROXIES=true no .env")
                        youtube_api_failed_permanently = True
                else:
                    # Se o erro não é de bloqueio, considera falha permanente para a API do YouTube
                    youtube_api_failed_permanently = True

        # Tenta Kome.ai (se YouTube falhou ou foi pulado)
        if transcript_text is None:
            try:
                transcript_text, source_lang = get_transcript_from_kome(video_id)
                source = "Kome.ai"
                logging.info(f"[{video_id}] Transcrição encontrada via Kome.ai ({source_lang})")
            except Exception as e2:
                error_str = str(e2)
                if "500 Server Error" in error_str:
                    logging.warning(f"[{video_id}] Kome.ai indisponível (500)")
                else:
                    logging.warning(f"[{video_id}] Falha Kome.ai: {error_str[:80]}")

        if transcript_text:
            file_path = os.path.join(output_dir, f"{video_id}_{source_lang}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            logging.info(f"[{video_id}] [SUCCESS] Transcrição salva ({source}) [{source_lang}] -> {file_path}")

            time.sleep(5)  # Delay para evitar sobrecarregar APIs
            return file_path

        retry_count += 1
        if retry_count < max_retries:
            logging.warning(f"[{video_id}] Tentativa {retry_count}/{max_retries} falhou. Retentando em 30s...")
            time.sleep(30)
        else:
            logging.error(f"[{video_id}] ❌ Todas as {max_retries} tentativas falharam. Vídeo sem transcrição disponível.")
            return None

