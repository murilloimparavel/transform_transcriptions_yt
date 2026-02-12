"""
Aplicação principal Streamlit.
"""
import streamlit as st
import sys
import os
import time

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

# Tenta importar componentes (pode falhar se não estiver no path correto)
try:
    from frontend.components.api_client import APIClient
    from frontend.components.progress_bar import show_job_progress
    import plotly.express as px
    import pandas as pd
    COMPONENTS_AVAILABLE = True
except ImportError:
    # Fallback se não conseguir importar
    COMPONENTS_AVAILABLE = False
    st.warning("⚠️ Alguns componentes não estão disponíveis. Verifique o path.")

# Configuração da página
st.set_page_config(
    page_title="YouTube Transcription Processor",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado e moderno
st.markdown("""
    <style>
    /* Fonte e Cores Globais */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Principal */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0E1117;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #FF4B4B 0%, #1f77b4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Cards de Estatísticas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Formulários e Inputs */
    .stTextInput > div > div > input {
        border-radius: 0.5rem;
    }
    .stSelectbox > div > div > div {
        border-radius: 0.5rem;
    }
    
    /* Botões */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Containers de Expansão */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: 0.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🎬 Transcription Processor")
    st.markdown("---")
    
    # Navegação com suporte a redirecionamento
    if "navigation_selector" not in st.session_state:
        st.session_state.navigation_selector = "Dashboard"
        
    page = st.selectbox(
        "Navegação",
        ["Dashboard", "Novo Processamento", "Resultados", "Configurações"],
        key="navigation_selector"
    )

# Inicializa cliente API
if COMPONENTS_AVAILABLE:
    if 'api_client' not in st.session_state:
        api_url = st.session_state.get('api_url', 'http://localhost:8000')
        st.session_state.api_client = APIClient(api_url)

# Páginas
if page == "Dashboard":
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    if not COMPONENTS_AVAILABLE:
        st.error("Componentes não disponíveis. Verifique as importações.")
    else:
        api_client = st.session_state.api_client
        
        # Verifica conexão com API
        if not api_client.health_check():
            st.error("⚠️ Não foi possível conectar à API. Verifique se a API está rodando em http://localhost:8000")
            st.info("💡 Para iniciar a API, execute: `python scripts/start_api.py`")
        else:
            # Busca dados da API
            all_jobs = api_client.get_jobs()
            completed_jobs = [j for j in all_jobs if j.get('status') == 'completed']
            processing_jobs = [j for j in all_jobs if j.get('status') == 'processing']
            pending_jobs = [j for j in all_jobs if j.get('status') == 'pending']
            
            # Calcula estatísticas
            total_processed = len(completed_jobs)
            total_processing = len(processing_jobs)
            total_videos = sum(j.get('total_videos', 0) for j in completed_jobs)
            processed_videos = sum(j.get('processed_videos', 0) for j in completed_jobs)
            success_rate = (processed_videos / total_videos * 100) if total_videos > 0 else 0
            
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Jobs Concluídos", total_processed)
            
            with col2:
                st.metric("Em Processamento", total_processing)
            
            with col3:
                st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
            
            with col4:
                st.metric("Total de Vídeos", total_videos)
            
            st.markdown("---")
            
            # Gráfico de status
            if all_jobs:
                status_counts = {}
                for job in all_jobs:
                    status = job.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                if status_counts:
                    df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Quantidade'])
                    fig = px.pie(df_status, values='Quantidade', names='Status', title='Distribuição de Status')
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Processamentos recentes
            st.subheader("📋 Processamentos Recentes")
            
            if all_jobs:
                # Mostra últimos 10 jobs
                recent_jobs = sorted(all_jobs, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
                
                for job in recent_jobs:
                    status_emoji = {
                        'completed': '✅',
                        'processing': '⏳',
                        'pending': '⏸️',
                        'failed': '❌',
                        'cancelled': '🚫'
                    }
                    
                    job_id = job.get('id', '')
                    status = job.get('status', 'unknown')
                    
                    with st.expander(
                        f"{status_emoji.get(status, '❓')} {job.get('source_type', 'N/A').upper()} - {job.get('prompt_type', 'N/A').upper()} ({job.get('progress', 0)}%)"
                    ):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ID:** {job_id[:8]}...")
                            st.write(f"**Status:** {status}")
                            st.write(f"**Progresso:** {job.get('progress', 0)}%")
                            st.write(f"**Fonte:** {job.get('source_id', 'N/A')[:50]}...")
                        with col2:
                            st.write(f"**Vídeos:** {job.get('processed_videos', 0)}/{job.get('total_videos', 0)}")
                            st.write(f"**Falhas:** {job.get('failed_videos', 0)}")
                            if job.get('created_at'):
                                st.write(f"**Criado:** {job.get('created_at', '')[:10]}")
                        
                        # Mostra progresso detalhado se estiver processando
                        if status == "processing":
                            st.markdown("---")
                            show_job_progress(job_id, api_client, auto_refresh=False)
            else:
                st.info("Nenhum processamento encontrado. Crie um novo processamento para começar.")

elif page == "Novo Processamento":
    st.markdown('<h1 class="main-header">🆕 Novo Processamento</h1>', unsafe_allow_html=True)
    
    if not COMPONENTS_AVAILABLE:
        st.error("Componentes não disponíveis.")
    else:
        api_client = st.session_state.api_client
        
        # Verifica conexão
        if not api_client.health_check():
            st.error("⚠️ Não foi possível conectar à API. Verifique se a API está rodando.")
        else:
            with st.form("new_processing_form"):
                st.subheader("🚀 Configuração do Novo Processamento")
                st.markdown("Preencha os dados abaixo para iniciar uma nova tarefa de transcrição e análise.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Tipo de fonte
                    source_type_map = {
                        "Playlist": "playlist",
                        "Canal": "canal",
                        "Documento": "documento",
                        "N8N Workflow (JSON)": "n8n"
                    }
                    source_type_display = st.selectbox(
                        "📂 Tipo de Fonte",
                        ["Playlist", "Canal", "Documento", "N8N Workflow (JSON)"],
                        help="Selecione a origem do conteúdo"
                    )
                    source_type = source_type_map[source_type_display]
                    
                    # Tipo de análise
                    prompt_type_map = {
                        "FAQ": "faq",
                        "Copywriting": "copywriting",
                        "Framework Completo": "framework",
                        "Documentação Técnica": "n8n_framework",
                        "PRD Completo (BMAD)": "prd"
                    }
                    prompt_options = ["FAQ", "Copywriting", "Framework Completo", "PRD Completo (BMAD)"]
                    if source_type == "n8n":
                        prompt_options = ["Documentação Técnica"]
                    
                    prompt_type_display = st.selectbox(
                        "🤖 Tipo de Análise",
                        prompt_options,
                        help="Escolha como a IA deve processar o conteúdo"
                    )
                    prompt_type = prompt_type_map[prompt_type_display]

                with col2:
                    # Idioma de saída
                    output_language_map = {
                        "Português (pt)": "pt",
                        "Inglês (en)": "en"
                    }
                    output_language_display = st.selectbox(
                        "🌐 Idioma de Saída",
                        ["Português (pt)", "Inglês (en)"],
                        help="Idioma em que o resultado será gerado"
                    )
                    output_language = output_language_map[output_language_display]
                    
                    # Idiomas preferidos
                    preferred_languages = st.text_input(
                        "🗣️ Idiomas do Vídeo (opcional)",
                        placeholder="pt,en",
                        help="Códigos dos idiomas falados no vídeo (ex: pt, en). Deixe vazio para automático."
                    )

                # ID/URL da fonte
                st.markdown("### 🔗 Link ou Caminho")
                
                source_id = ""
                if source_type == "n8n":
                    uploaded_file = st.file_uploader("Upload JSON do Workflow", type=['json'])
                    if uploaded_file:
                        # Salva arquivo
                        uploads_dir = os.path.join("data", "uploads")
                        os.makedirs(uploads_dir, exist_ok=True)
                        file_path = os.path.join(uploads_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        source_id = file_path
                        st.success(f"Arquivo salvo em: {source_id}")
                else:
                    source_id = st.text_input(
                        "URL ou ID",
                        placeholder="https://www.youtube.com/playlist?list=..." if source_type == "playlist" else "https://www.youtube.com/channel/..." if source_type == "canal" else "caminho/do/arquivo.xlsx",
                        label_visibility="collapsed"
                    )
                
                st.markdown("---")
                submitted = st.form_submit_button("✨ Iniciar Processamento", use_container_width=True, type="primary")
                
                if submitted:
                    if not source_id:
                        st.error("❌ Por favor, informe a URL ou ID da fonte.")
                    else:
                        # Cria job
                        job_data = {
                            "source_type": source_type,
                            "source_id": source_id,
                            "prompt_type": prompt_type,
                            "output_language": output_language,
                            "preferred_languages": preferred_languages if preferred_languages else None
                        }
                        
                        with st.spinner("🔄 Criando job..."):
                            job = api_client.create_job(job_data)
                        
                        if job:
                            st.success(f"✅ Job criado com sucesso! ID: {job.get('id', 'N/A')[:8]}...")
                            
                            # Inicia processamento
                            with st.spinner("🚀 Iniciando processamento..."):
                                process_result = api_client.start_processing(job['id'])
                            
                            if process_result:
                                st.success("🎉 Processamento iniciado!")
                                st.info(f"Você pode acompanhar o progresso no Dashboard. Job ID: {job['id']}")
                                st.balloons()
                                time.sleep(2)
                                # Redireciona para o Dashboard
                                st.session_state.navigation_selector = "Dashboard"
                                st.rerun()
                            else:
                                st.warning("⚠️ Job criado, mas não foi possível iniciar o processamento automaticamente.")
                        else:
                            st.error("❌ Erro ao criar job. Verifique os dados e tente novamente.")

elif page == "Resultados":
    st.markdown('<h1 class="main-header">📄 Resultados</h1>', unsafe_allow_html=True)
    
    if not COMPONENTS_AVAILABLE:
        st.error("Componentes não disponíveis.")
    else:
        api_client = st.session_state.api_client
        
        if not api_client.health_check():
            st.error("⚠️ Não foi possível conectar à API.")
        else:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                result_type_filter = st.selectbox("Tipo", ["Todos", "FAQ", "Copywriting", "Framework", "PRD"])
            with col2:
                search = st.text_input("Buscar", placeholder="Digite para buscar...")
            
            st.markdown("---")
            
            # Busca resultados
            result_type = None if result_type_filter == "Todos" else result_type_filter.lower()
            if result_type == "prd": result_type = "prd_bmad"  # Mapeamento para filtro da API se necessário
            results = api_client.get_results(result_type=result_type)
            
            if results:
                st.subheader(f"📋 {len(results)} Resultado(s) Encontrado(s)")
                
                for result in results:
                    with st.expander(
                        f"📄 {result.get('result_type', 'N/A').upper()} - {result.get('file_path', 'N/A').split('/')[-1]}"
                    ):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**ID:** {result.get('id', 'N/A')[:8]}...")
                            st.write(f"**Tipo:** {result.get('result_type', 'N/A')}")
                            if result.get('content_preview'):
                                st.text_area(
                                    "Preview",
                                    result.get('content_preview', ''),
                                    height=200,
                                    disabled=True
                                )
                        
                        with col2:
                            if result.get('file_path'):
                                st.write(f"**Arquivo:** {result.get('file_path', '').split('/')[-1]}")
                            if result.get('created_at'):
                                st.write(f"**Criado:** {result.get('created_at', '')[:10]}")
                            
                            # Botão de download
                            if result.get('file_path'):
                                try:
                                    with open(result.get('file_path'), 'rb') as f:
                                        st.download_button(
                                            "⬇️ Download",
                                            f.read(),
                                            file_name=result.get('file_path', '').split('/')[-1],
                                            mime="text/plain"
                                        )
                                except:
                                    st.warning("Arquivo não encontrado")
            else:
                st.info("Nenhum resultado encontrado. Processe alguns vídeos primeiro.")

elif page == "Configurações":
    st.markdown('<h1 class="main-header">⚙️ Configurações</h1>', unsafe_allow_html=True)
    
    st.subheader("Configurações da API")
    
    # Inicializa API URL se não existir
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "http://localhost:8000"
    
    with st.form("settings_form"):
        api_url = st.text_input(
            "URL da API",
            value=st.session_state.api_url,
            help="URL base da API FastAPI"
        )
        
        submitted = st.form_submit_button("💾 Salvar Configurações")
        
        if submitted:
            st.session_state.api_url = api_url
            st.session_state.api_client = APIClient(api_url)
            st.success("✅ Configurações salvas!")
            
            # Testa conexão
            if st.session_state.api_client.health_check():
                st.success("✅ Conexão com API estabelecida!")
            else:
                st.warning("⚠️ Não foi possível conectar à API. Verifique a URL.")
    
    st.markdown("---")
    
    st.subheader("Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configurações da Aplicação**")
        st.json({
            "LLM Model": settings.llm_model,
            "Database": settings.database_url,
            "Use Proxies": settings.use_proxies,
            "Max Retries": settings.max_retries,
            "Chunk Size": settings.chunk_size
        })
    
    with col2:
        st.write("**Status da API**")
        if COMPONENTS_AVAILABLE:
            api_client = st.session_state.api_client
            if api_client.health_check():
                health = api_client._get("/health")
                st.success("✅ API Online")
                st.json(health if health else {"status": "unknown"})
            else:
                st.error("❌ API Offline")
                st.info("Execute `python scripts/start_api.py` para iniciar a API")
        else:
            st.warning("Componentes não disponíveis")

if __name__ == "__main__":
    pass

