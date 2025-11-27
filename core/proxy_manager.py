"""
Gerenciador de proxies para evitar bloqueio de IP do YouTube.
Suporta proxies gratuitos, rotativos e persistência de bons/ruins.
"""

import os
import json
import requests
import random
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Gerencia lista de proxies e rotação automática com persistência.
    """

    def __init__(self, use_proxies=False):
        self.use_proxies = use_proxies
        self.proxies = []
        self.current_index = 0
        self.failed_proxies = set()
        self.last_fetch = None
        self.cache_duration = timedelta(minutes=30)
        
        # Persistência
        self.data_dir = "data/proxies"
        self.good_file = os.path.join(self.data_dir, "good_proxies.json")
        self.bad_file = os.path.join(self.data_dir, "bad_proxies.json")
        
        self.good_proxies = {}  # {proxy: timestamp}
        self.bad_proxies = {}   # {proxy: timestamp}
        
        if self.use_proxies:
            self._ensure_dir()
            self._load_lists()

    def _ensure_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_lists(self):
        """Carrega listas de persistência do disco."""
        try:
            if os.path.exists(self.good_file):
                with open(self.good_file, 'r') as f:
                    self.good_proxies = json.load(f)
            
            if os.path.exists(self.bad_file):
                with open(self.bad_file, 'r') as f:
                    self.bad_proxies = json.load(f)
                    
            # Limpeza automática: remove bad proxies antigos (> 1 hora)
            now = datetime.now().timestamp()
            one_hour = 3600
            self.bad_proxies = {p: t for p, t in self.bad_proxies.items() if now - t < one_hour}
            
        except Exception as e:
            logger.warning(f"⚠️  Erro ao carregar listas de proxies: {e}")

    def _save_lists(self):
        """Salva listas de persistência no disco."""
        try:
            with open(self.good_file, 'w') as f:
                json.dump(self.good_proxies, f, indent=2)
            
            with open(self.bad_file, 'w') as f:
                json.dump(self.bad_proxies, f, indent=2)
        except Exception as e:
            logger.warning(f"⚠️  Erro ao salvar listas de proxies: {e}")

    def mark_proxy_success(self, proxy):
        """Marca um proxy como funcional e o salva."""
        if not proxy: return
        
        self.good_proxies[proxy] = datetime.now().timestamp()
        # Se estava na lista ruim, remove
        if proxy in self.bad_proxies:
            del self.bad_proxies[proxy]
            
        self._save_lists()
        logger.info(f"🌟 Proxy promovido para lista VIP: {proxy}")

    def mark_proxy_failed(self, proxy):
        """Marca um proxy como falho e o salva na blacklist temporária."""
        if not proxy: return
        
        self.failed_proxies.add(proxy)
        self.bad_proxies[proxy] = datetime.now().timestamp()
        
        # Se estava na lista boa, remove
        if proxy in self.good_proxies:
            del self.good_proxies[proxy]
            
        self._save_lists()
        # Log apenas no arquivo (INFO não aparece no console)
        logger.info(f"❌ Proxy marcado como falho: {proxy}")

        # Se muitos falharam da lista atual, tenta refetch
        if len(self.failed_proxies) >= len(self.proxies) * 0.7:
            logger.info("🔄 Muitos proxies falharam, buscando nova lista...")
            self.load_proxies()

    def is_bad_proxy(self, proxy):
        """Verifica se o proxy está na blacklist recente."""
        return proxy in self.bad_proxies

    def fetch_free_proxies(self, source="proxifly"):
        """
        Busca lista de proxies gratuitos de fontes públicas.
        """
        logger.info(f"🔍 Buscando proxies gratuitos de: {source}")

        proxies = []
        if source == "br":
            proxies = self._fetch_br_proxies()
        elif source == "proxifly":
            proxies = self._fetch_from_proxifly()
        elif source == "proxyscrape":
            proxies = self._fetch_from_proxyscrape()
        elif source == "manual":
            proxies = self._fetch_from_env()
        
        # Filtra proxies ruins
        valid_proxies = [p for p in proxies if not self.is_bad_proxy(p)]
        
        diff = len(proxies) - len(valid_proxies)
        if diff > 0:
            logger.info(f"🗑️  {diff} proxies removidos por estarem na blacklist recente.")
            
        return valid_proxies

    def _format_proxy_url(self, line):
        line = line.strip()
        if not line: return None

        # Filtra apenas HTTP/HTTPS (SOCKS não funciona com requests diretamente)
        if line.startswith('socks'):
            return None

        if line.startswith(('http://', 'https://')):
            return line
        return f"http://{line}"

    def _fetch_br_proxies(self):
        proxies = []
        try:
            url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/BR/data.txt"
            logger.info("🇧🇷 Buscando proxies BR no Proxifly...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    proxy = self._format_proxy_url(line)
                    if proxy and ':' in proxy: proxies.append(proxy)
                logger.info(f"✅ Encontrados {len(proxies)} proxies BR no Proxifly")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao buscar BR no Proxifly: {e}")

        if len(proxies) < 5:
            try:
                logger.info("🇧🇷 Buscando proxies BR complementares no ProxyScrape...")
                url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=BR&ssl=all&anonymity=all"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    for line in response.text.strip().split('\n'):
                        proxy = self._format_proxy_url(line)
                        if proxy and ':' in proxy and proxy not in proxies:
                            proxies.append(proxy)
                    logger.info(f"✅ Total de proxies BR: {len(proxies)}")
            except Exception as e:
                logger.warning(f"⚠️  Erro ao buscar BR no ProxyScrape: {e}")
        
        random.shuffle(proxies)
        return proxies

    def _fetch_from_proxifly(self):
        """
        Busca proxies HTTP/HTTPS do Proxifly (fonte global).
        Combina HTTP + HTTPS para ter pool maior.
        """
        try:
            all_proxies = []

            # 1. Proxies HTTP
            url_http = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"
            logger.info("📥 Baixando proxies HTTP do Proxifly...")
            response = requests.get(url_http, timeout=15)
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    proxy = self._format_proxy_url(line)
                    if proxy and ':' in proxy: all_proxies.append(proxy)

            logger.info(f"✅ {len(all_proxies)} proxies HTTP carregados")

            # 2. Proxies HTTPS
            url_https = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/https/data.txt"
            logger.info("📥 Baixando proxies HTTPS do Proxifly...")
            response_https = requests.get(url_https, timeout=15)
            if response_https.status_code == 200:
                for line in response_https.text.strip().split('\n'):
                    proxy = self._format_proxy_url(line)
                    if proxy and ':' in proxy and proxy not in all_proxies:
                        all_proxies.append(proxy)

            logger.info(f"✅ Total: {len(all_proxies)} proxies (HTTP + HTTPS)")

            # Embaralha para distribuir entre países
            random.shuffle(all_proxies)

            # Retorna 300 proxies para aumentar chances (taxa ~1-5%)
            return all_proxies[:300]

        except Exception as e:
            logger.error(f"❌ Erro ao buscar proxies do Proxifly: {e}")
            return []

    def _fetch_from_proxyscrape(self):
        try:
            url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
            response = requests.get(url, timeout=10)
            proxies = []
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    proxy = self._format_proxy_url(line)
                    if proxy and ':' in proxy: proxies.append(proxy)
            logger.info(f"✅ {len(proxies)} proxies do ProxyScrape")
            return proxies[:50]
        except Exception:
            return []

    def _fetch_from_env(self):
        proxy_list = os.environ.get("PROXIES", "").split(',')
        proxies = [p.strip() for p in proxy_list if p.strip()]
        if proxies: logger.info(f"✅ {len(proxies)} proxies manuais")
        return proxies

    def load_proxies(self, source="proxifly", validate=True, min_proxies=15):
        """
        Carrega lista de proxies com prioridade para 'Good Proxies'.

        Args:
            source: Fonte dos proxies (proxifly, br, manual, etc)
            validate: Se True, testa proxies em massa antes de usar (recomendado)
            min_proxies: Número mínimo de proxies para manter na lista (padrão: 15)
        """
        # 1. Tenta usar proxies conhecidos e bons (usados nas últimas 24h)
        now = datetime.now().timestamp()
        day = 86400
        valid_good = [p for p, t in self.good_proxies.items() if now - t < day]

        # Se tem proxies VIP suficientes, usa eles
        if len(valid_good) >= min_proxies and not self.proxies:
            logger.info(f"💎 Carregando {len(valid_good)} proxies da lista VIP...")
            self.proxies = valid_good
            random.shuffle(self.proxies)
            self.use_proxies = True
            self.failed_proxies.clear()
            logger.info(f"✅ {len(self.proxies)} proxies VIP prontos!")
            return

        # Se tem alguns VIPs mas não o suficiente, avisa e busca mais
        if valid_good and len(valid_good) < min_proxies:
            logger.info(f"⚠️  Apenas {len(valid_good)} proxies VIP - buscando mais para atingir mínimo de {min_proxies}...")

        # 2. Busca novos proxies da fonte
        new_proxies = self.fetch_free_proxies(source)

        if new_proxies:
            # Remove proxies que já estão na lista VIP para não re-testar
            new_proxies = [p for p in new_proxies if p not in self.good_proxies]

            if not new_proxies:
                logger.info("ℹ️  Todos os proxies desta fonte já estão validados")
                if valid_good:
                    self.proxies = valid_good
                    random.shuffle(self.proxies)
                    self.use_proxies = True
                return

            # 🚀 Valida proxies em massa antes de usar
            if validate and len(new_proxies) > 5:
                logger.info(f"🔍 Validando {len(new_proxies)} proxies novos...")
                validated_proxies = self.test_proxies_bulk(new_proxies, max_workers=30, timeout=3)

                if validated_proxies:
                    # 🎯 ACUMULA os bons na lista VIP (não substitui!)
                    now = datetime.now().timestamp()
                    for proxy in validated_proxies:
                        self.good_proxies[proxy] = now
                    self._save_lists()

                    # Combina VIPs antigos + novos validados
                    all_working = valid_good + validated_proxies
                    self.proxies = all_working
                    random.shuffle(self.proxies)

                    logger.info(f"✅ {len(validated_proxies)} novos proxies validados!")
                    logger.info(f"💎 Total na lista VIP: {len(self.good_proxies)} proxies")
                    logger.info(f"🎯 Usando {len(self.proxies)} proxies para esta sessão")
                else:
                    logger.warning("⚠️  Nenhum proxy novo passou na validação")
                    if valid_good:
                        logger.info(f"📦 Usando {len(valid_good)} proxies VIP existentes")
                        self.proxies = valid_good
                    else:
                        logger.warning("⚠️  Sem proxies validados - usando lista não validada")
                        self.proxies = new_proxies
            else:
                # Sem validação - combina VIPs + novos
                all_proxies = valid_good + new_proxies
                self.proxies = all_proxies
                random.shuffle(self.proxies)
                logger.info(f"✅ {len(self.proxies)} proxies carregados ({source})")

            self.current_index = 0
            self.failed_proxies.clear()
            self.last_fetch = datetime.now()
            self.use_proxies = True
        else:
            # Sem novos proxies - usa VIPs se tiver
            if valid_good:
                logger.info(f"📦 Fonte '{source}' vazia - usando {len(valid_good)} proxies VIP")
                self.proxies = valid_good
                random.shuffle(self.proxies)
                self.use_proxies = True
            else:
                # Apenas log de DEBUG - não é erro, pode ter fallback
                if source == "manual":
                    logger.debug(f"ℹ️  Nenhum proxy manual configurado no .env (normal)")
                else:
                    logger.warning(f"⚠️  Fonte '{source}' não retornou proxies")

    def get_next_proxy(self):
        if not self.use_proxies or not self.proxies:
            return None

        attempts = 0
        max_attempts = len(self.proxies)

        while attempts < max_attempts:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            attempts += 1

            if proxy in self.failed_proxies:
                continue

            return proxy

        logger.warning("⚠️  Todos os proxies falharam, resetando lista...")
        self.failed_proxies.clear()
        return self.proxies[0] if self.proxies else None

    def get_proxy_dict(self, proxy_url):
        if not proxy_url: return None
        return {"http": proxy_url, "https": proxy_url}

    def test_proxy(self, proxy_url, timeout=5):
        """
        Testa um proxy individual contra o YouTube.

        Testa especificamente contra youtube.com para garantir que
        o proxy não está bloqueado pelo YouTube.
        """
        try:
            proxies = self.get_proxy_dict(proxy_url)
            # 🎯 Testa contra YouTube diretamente (mais rigoroso)
            response = requests.get(
                "https://www.youtube.com",
                proxies=proxies,
                timeout=timeout,
                allow_redirects=True
            )
            # Verifica se não está bloqueado (YouTube retorna 200 ou 302)
            return response.status_code in [200, 302, 301]
        except:
            return False

    def test_proxies_bulk(self, proxy_list, max_workers=20, timeout=3):
        """
        Testa múltiplos proxies em paralelo (MUITO MAIS RÁPIDO).

        Args:
            proxy_list: Lista de URLs de proxies
            max_workers: Número de threads paralelas (padrão: 20)
            timeout: Timeout por proxy em segundos (padrão: 3s)

        Returns:
            list: Lista de proxies que funcionam
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        import sys

        working_proxies = []
        total = len(proxy_list)

        logger.info(f"🧪 Testando {total} proxies em paralelo ({max_workers} threads)...")
        start_time = time.time()

        def test_single(proxy):
            """
            Testa um proxy contra o YouTube e retorna (proxy, is_working).

            🎯 IMPORTANTE: Testa contra youtube.com, não google.com,
            para garantir que o proxy funciona especificamente com YouTube.
            """
            try:
                proxies_dict = self.get_proxy_dict(proxy)
                response = requests.get(
                    "https://www.youtube.com",
                    proxies=proxies_dict,
                    timeout=timeout,
                    allow_redirects=True
                )
                # YouTube retorna 200, 301, ou 302 quando funciona
                if response.status_code in [200, 301, 302]:
                    return (proxy, True)
            except:
                pass
            return (proxy, False)

        # Testa em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete todas as tarefas
            futures = {executor.submit(test_single, proxy): proxy for proxy in proxy_list}

            # Coleta resultados conforme completam
            completed = 0
            for future in as_completed(futures):
                completed += 1
                proxy, is_working = future.result()

                if is_working:
                    working_proxies.append(proxy)

                # 🎯 BARRA DE PROGRESSO no console
                percentage = (completed / total) * 100
                bar_length = 40
                filled = int(bar_length * completed / total)
                bar = '█' * filled + '░' * (bar_length - filled)

                # Atualiza a mesma linha
                sys.stdout.write(f'\r   [{bar}] {completed}/{total} ({percentage:.1f}%) | ✅ {len(working_proxies)} funcionando')
                sys.stdout.flush()

        # Nova linha após completar
        print()

        elapsed = time.time() - start_time
        success_rate = (len(working_proxies) / total * 100) if total > 0 else 0

        logger.info(f"")
        logger.info(f"📊 Resultado do teste em massa:")
        logger.info(f"   • Tempo total: {elapsed:.1f}s")
        logger.info(f"   • Testados: {total}")
        logger.info(f"   • ✅ Funcionando: {len(working_proxies)} ({success_rate:.1f}%)")
        logger.info(f"   • ❌ Falharam: {total - len(working_proxies)}")

        return working_proxies

    def get_working_proxy(self, max_tests=5):
        for _ in range(max_tests):
            proxy = self.get_next_proxy()
            if not proxy: break
            logger.info(f"🧪 Testando proxy: {proxy}")
            if self.test_proxy(proxy):
                logger.info(f"✅ Proxy funcionando: {proxy}")
                return proxy
            else:
                self.mark_proxy_failed(proxy)
        return None


# Singleton global
_proxy_manager = None


def get_proxy_manager(use_proxies=False, min_proxies=5):
    """
    Retorna instância singleton do ProxyManager com garantia de proxies mínimos.

    Args:
        use_proxies: Se deve usar proxies
        min_proxies: Número mínimo de proxies para manter (padrão: 15)
    """
    global _proxy_manager

    if _proxy_manager is None:
        _proxy_manager = ProxyManager(use_proxies)
        if use_proxies:
            logger.info(f"🔄 Inicializando sistema de proxies (mínimo: {min_proxies})...")

            # Tenta manual primeiro (se configurado no .env)
            _proxy_manager.load_proxies("manual", validate=False, min_proxies=min_proxies)

            # Se não atingiu o mínimo, busca GLOBAL (melhor taxa de sucesso)
            if len(_proxy_manager.proxies) < min_proxies:
                logger.info("🌍 Buscando proxies GLOBAIS (HTTP + HTTPS)...")
                _proxy_manager.load_proxies("proxifly", validate=True, min_proxies=min_proxies)

            # Se ainda não atingiu, tenta ProxyScrape
            if len(_proxy_manager.proxies) < min_proxies:
                _proxy_manager.load_proxies("proxyscrape", validate=True, min_proxies=min_proxies)

            # Última tentativa: BR (menor pool)
            if len(_proxy_manager.proxies) < min_proxies:
                _proxy_manager.load_proxies("br", validate=True, min_proxies=min_proxies)

            # Relatório final
            if _proxy_manager.proxies:
                logger.info(f"✅ Sistema de proxies pronto com {len(_proxy_manager.proxies)} proxies validados")
                if len(_proxy_manager.proxies) < min_proxies:
                    logger.warning(f"⚠️  Apenas {len(_proxy_manager.proxies)} proxies (meta: {min_proxies}) - sistema vai usar o que tem")
            else:
                logger.warning("⚠️  Nenhum proxy validado - sistema vai usar Kome.ai")
                _proxy_manager.use_proxies = False  # Desativa se não tem nenhum

    else:
        # Singleton já existe - USA O QUE TEM (não recarrega)
        if use_proxies:
            if _proxy_manager.proxies:
                logger.info(f"💎 Usando {len(_proxy_manager.proxies)} proxies do cache (singleton)")
            elif len(_proxy_manager.proxies) == 0:
                # Só recarrega se estiver VAZIO
                logger.warning("⚠️  Cache vazio - recarregando proxies...")
                _proxy_manager.use_proxies = True
                _proxy_manager.load_proxies("proxifly", validate=True, min_proxies=min_proxies)

    return _proxy_manager


def enable_proxies():
    manager = get_proxy_manager(use_proxies=True)
    manager.use_proxies = True
    manager.load_proxies()
    logger.info("🔄 Sistema de proxies ativado")


def disable_proxies():
    manager = get_proxy_manager()
    manager.use_proxies = False
    logger.info("⏸️  Sistema de proxies desativado")
