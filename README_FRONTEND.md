# 🚀 Guia de Início Rápido - Frontend e API

## 📋 Status da Implementação

### ✅ Concluído
- [x] PRD (Product Requirements Document)
- [x] Arquitetura do Sistema
- [x] Estrutura base da API FastAPI
- [x] Modelos de banco de dados (SQLAlchemy)
- [x] Frontend Streamlit básico
- [x] Sistema de configuração centralizado (Pydantic Settings)
- [x] Rotas básicas da API

### ⏳ Em Desenvolvimento
- [ ] Integração completa frontend-backend
- [ ] Sistema de filas (Celery)
- [ ] WebSocket para progresso em tempo real
- [ ] Dashboard com dados reais
- [ ] Processamento assíncrono

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Certifique-se de que o arquivo `.env` existe e contém:

```env
API_KEY=sua_chave_gemini
YOUTUBE_API_KEY=sua_chave_youtube
LLM_MODEL=gemini-2.5-flash
USE_PROXIES=false

# Database (opcional - padrão SQLite)
DATABASE_URL=sqlite:///./data/app.db

# Redis (para Celery - futuro)
REDIS_URL=redis://localhost:6379/0
```

### 3. Inicializar Banco de Dados

```bash
python -c "from api.database.database import init_db; init_db()"
```

Ou simplesmente execute a API uma vez (ela cria automaticamente).

### 4. Executar a API

```bash
# Opção 1: Direto
python api/main.py

# Opção 2: Com uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000
Documentação: http://localhost:8000/docs

### 5. Executar o Frontend

```bash
streamlit run frontend/app.py
```

O frontend estará disponível em: http://localhost:8501

## 📁 Estrutura Criada

```
transform_transcriptions_yt/
├── api/                          # Backend FastAPI
│   ├── main.py                  # App principal
│   ├── routes/                  # Rotas da API
│   │   ├── jobs.py              # CRUD de jobs
│   │   ├── videos.py
│   │   ├── results.py
│   │   └── processing.py
│   ├── services/                 # Lógica de negócio
│   │   └── job_service.py
│   ├── models/                   # Modelos Pydantic
│   │   └── job.py
│   └── database/                 # Database
│       ├── database.py
│       └── models.py
│
├── frontend/                      # Frontend Streamlit
│   └── app.py                    # App principal
│
├── config/                        # Configurações
│   └── settings.py               # Pydantic Settings
│
└── docs/                          # Documentação
    ├── PRD_FRONTEND.md
    └── ARCHITECTURE.md
```

## 🔌 Endpoints da API

### Jobs
- `POST /api/jobs` - Criar novo job
- `GET /api/jobs` - Listar jobs
- `GET /api/jobs/{id}` - Detalhes do job
- `PATCH /api/jobs/{id}` - Atualizar job
- `DELETE /api/jobs/{id}` - Deletar job
- `GET /api/jobs/{id}/progress` - Progresso do job

### Health
- `GET /` - Informações da API
- `GET /health` - Health check

## 🧪 Testar a API

### Criar um Job

```bash
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "playlist",
    "source_id": "https://www.youtube.com/playlist?list=...",
    "prompt_type": "faq",
    "output_language": "pt",
    "preferred_languages": "pt,en"
  }'
```

### Listar Jobs

```bash
curl "http://localhost:8000/api/jobs"
```

### Ver Progresso

```bash
curl "http://localhost:8000/api/jobs/{job_id}/progress"
```

## 📝 Próximos Passos

1. **Integrar processamento real**: Conectar API com código existente em `core/`
2. **Implementar Celery**: Sistema de filas para processamento assíncrono
3. **WebSocket**: Progresso em tempo real
4. **Frontend completo**: Integrar com API real
5. **Testes**: Unit e integration tests
6. **Docker**: Containerização

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"
Certifique-se de estar no diretório raiz do projeto e que todas as dependências estão instaladas.

### Erro: "Database not found"
Execute a inicialização do banco de dados ou simplesmente inicie a API (ela cria automaticamente).

### Erro: "Port already in use"
Altere as portas no arquivo `config/settings.py` ou nas variáveis de ambiente.

## 📚 Documentação Adicional

- [PRD](./docs/PRD_FRONTEND.md) - Product Requirements Document
- [Arquitetura](./docs/ARCHITECTURE.md) - Arquitetura do Sistema
- [README Principal](./README.md) - Documentação original

---

**Desenvolvido seguindo metodologia BMAD** 🚀

