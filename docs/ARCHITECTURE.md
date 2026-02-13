# 🏗️ Arquitetura do Sistema - Frontend e Melhorias

## 1. Visão Geral da Arquitetura

### 1.1. Arquitetura em Camadas

```
┌─────────────────────────────────────────────────┐
│           Frontend Layer (Streamlit)           │
│  - Dashboard, Upload, Progress, Results        │
└───────────────────┬─────────────────────────────┘
                    │ HTTP/WebSocket
┌───────────────────▼─────────────────────────────┐
│         API Layer (FastAPI)                     │
│  - REST Endpoints, WebSocket, Auth              │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│      Business Logic Layer                       │
│  - Services, Processors, Validators             │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌─────────▼─────────┐
│   Database     │    │  Queue System     │
│   (SQLite/     │    │  (Celery+Redis)   │
│   PostgreSQL)  │    │                   │
└────────────────┘    └───────────────────┘
```

## 2. Estrutura de Diretórios

```
transform_transcriptions_yt/
├── frontend/                    # Frontend Streamlit
│   ├── app.py                  # App principal Streamlit
│   ├── pages/                   # Páginas do Streamlit
│   │   ├── dashboard.py
│   │   ├── process.py
│   │   ├── results.py
│   │   └── settings.py
│   └── components/              # Componentes reutilizáveis
│       ├── progress_bar.py
│       ├── video_list.py
│       └── stats_card.py
│
├── api/                         # Backend FastAPI
│   ├── main.py                  # App FastAPI
│   ├── routes/                  # Rotas da API
│   │   ├── jobs.py              # CRUD de jobs
│   │   ├── videos.py            # Gerenciamento de vídeos
│   │   ├── processing.py        # Processamento
│   │   ├── results.py           # Resultados
│   │   └── websocket.py         # WebSocket
│   ├── services/                # Lógica de negócio
│   │   ├── job_service.py
│   │   ├── video_service.py
│   │   ├── processing_service.py
│   │   └── transcription_service.py
│   ├── models/                  # Modelos Pydantic
│   │   ├── job.py
│   │   ├── video.py
│   │   └── result.py
│   └── database/                # Database
│       ├── models.py            # SQLAlchemy models
│       ├── database.py          # Configuração DB
│       └── repositories.py      # Repositórios
│
├── workers/                      # Workers Celery
│   ├── celery_app.py
│   ├── tasks.py                  # Tarefas assíncronas
│   └── processors/              # Processadores
│       ├── video_processor.py
│       └── transcription_processor.py
│
├── core/                        # Código existente (refatorado)
│   ├── transcription.py
│   ├── processing.py
│   └── ...
│
├── config/                      # Configurações
│   ├── settings.py              # Pydantic Settings
│   └── prompts/
│
└── tests/                       # Testes
    ├── unit/
    ├── integration/
    └── fixtures/
```

## 3. Componentes Principais

### 3.1. Frontend (Streamlit)

#### Dashboard (`pages/dashboard.py`)
- Estatísticas gerais
- Gráficos de uso
- Lista de processamentos recentes
- Ações rápidas

#### Processamento (`pages/process.py`)
- Formulário de upload
- Configuração de opções
- Iniciar processamento
- Visualizar progresso

#### Resultados (`pages/results.py`)
- Lista de resultados
- Filtros e busca
- Preview de conteúdo
- Download

### 3.2. API (FastAPI)

#### Endpoints Principais

```
POST   /api/jobs                 # Criar novo job
GET    /api/jobs                 # Listar jobs
GET    /api/jobs/{id}            # Detalhes do job
DELETE /api/jobs/{id}            # Cancelar job
GET    /api/jobs/{id}/progress   # Progresso do job

POST   /api/videos/upload        # Upload de vídeo/playlist
GET    /api/videos               # Listar vídeos

GET    /api/results              # Listar resultados
GET    /api/results/{id}         # Detalhes do resultado
GET    /api/results/{id}/download # Download

WS     /ws/jobs/{id}             # WebSocket para progresso
```

### 3.3. Banco de Dados

#### Modelos SQLAlchemy

```python
# database/models.py

class ProcessingJob(Base):
    id: UUID
    source_type: str  # playlist, canal, documento
    source_id: str
    prompt_type: str  # faq, copywriting, framework
    output_language: str
    status: str  # pending, processing, completed, failed
    created_at: datetime
    updated_at: datetime
    progress: int  # 0-100
    total_videos: int
    processed_videos: int

class Video(Base):
    id: UUID
    job_id: UUID
    video_url: str
    video_id: str
    title: str
    status: str
    transcription_path: str
    error_message: str

class Transcription(Base):
    id: UUID
    video_id: UUID
    content: str
    language: str
    created_at: datetime

class Result(Base):
    id: UUID
    job_id: UUID
    video_id: UUID
    result_type: str  # faq, copywriting, framework
    content: str
    file_path: str
    created_at: datetime
```

### 3.4. Sistema de Filas (Celery)

```python
# workers/tasks.py

@celery_app.task
def process_video_async(video_url, job_id, config):
    """Processa um vídeo de forma assíncrona"""
    pass

@celery_app.task
def process_job_async(job_id):
    """Processa um job completo (múltiplos vídeos)"""
    pass
```

## 4. Fluxo de Dados

### 4.1. Processamento de Vídeo

```
1. Usuário cria job via Frontend
   ↓
2. Frontend → API POST /api/jobs
   ↓
3. API cria job no DB (status: pending)
   ↓
4. API envia tarefa para Celery
   ↓
5. Worker Celery processa:
   - Download transcrição
   - Processamento com IA
   - Salva resultado
   - Atualiza progresso no DB
   ↓
6. WebSocket notifica Frontend
   ↓
7. Frontend atualiza UI
```

### 4.2. Visualização de Progresso

```
1. Frontend conecta WebSocket
   ↓
2. Worker atualiza progresso no DB
   ↓
3. API lê progresso do DB
   ↓
4. API envia via WebSocket
   ↓
5. Frontend atualiza barra de progresso
```

## 5. Integração com Código Existente

### 5.1. Refatoração Gradual

- Manter `core/` funcionando
- Criar wrappers na camada de serviços
- Migrar gradualmente para nova arquitetura
- Manter compatibilidade durante transição

### 5.2. Adaptadores

```python
# api/services/transcription_service.py

class TranscriptionService:
    def __init__(self):
        # Usa código existente
        from core.transcription import download_transcription
        self._download = download_transcription
    
    def download(self, video_url, config):
        # Adiciona lógica nova (DB, logging, etc)
        result = self._download(video_url, config)
        # Salva no DB
        return result
```

## 6. Configuração e Deploy

### 6.1. Docker Compose

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
  
  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  worker:
    build: ./workers
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
```

### 6.2. Variáveis de Ambiente

```env
# Database
DATABASE_URL=sqlite:///./data/app.db
# ou
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_KEY=...
YOUTUBE_API_KEY=...
LLM_MODEL=gemini-2.5-flash

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 7. Segurança

### 7.1. Validação
- Pydantic models para validação
- Sanitização de inputs
- Rate limiting

### 7.2. Autenticação (Futuro)
- JWT tokens
- OAuth2
- Role-based access control

## 8. Monitoramento

### 8.1. Logging
- Estruturado (JSON)
- Níveis apropriados
- Rotação de logs

### 8.2. Métricas
- Tempo de processamento
- Taxa de sucesso
- Uso de recursos
- Erros e exceções

## 9. Testes

### 9.1. Estratégia
- Unit tests para serviços
- Integration tests para API
- E2E tests para fluxos críticos

### 9.2. Cobertura
- Meta: 80%+ de cobertura
- Foco em lógica de negócio
- Testes de API endpoints

---

**Versão**: 1.0  
**Data**: 2025-01-27  
**Autor**: Sistema BMAD

