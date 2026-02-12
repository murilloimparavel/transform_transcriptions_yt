# 🚀 Guia de Início Rápido Completo

## 📋 Pré-requisitos

- Python 3.11+
- Redis (para Celery - opcional, mas recomendado)
- Chaves API configuradas no `.env`

## 🔧 Instalação

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

# Database (opcional)
DATABASE_URL=sqlite:///./data/app.db

# Redis (para Celery - opcional)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Inicializar Banco de Dados

```bash
python scripts/init_db.py
```

## 🎯 Modo de Uso

### Opção 1: Frontend Web (Recomendado)

#### 1. Iniciar API

```bash
# Terminal 1
python scripts/start_api.py
```

A API estará em: http://localhost:8000
Documentação: http://localhost:8000/docs

#### 2. Iniciar Worker (Opcional - para processamento assíncrono)

```bash
# Terminal 2 (se usar Celery)
# Primeiro, inicie Redis:
redis-server

# Depois, inicie o worker:
python scripts/start_worker.py
```

#### 3. Iniciar Frontend

```bash
# Terminal 3
python scripts/start_frontend.py
```

O frontend estará em: http://localhost:8501

#### 4. Usar a Interface

1. Acesse http://localhost:8501
2. Vá para "Novo Processamento"
3. Preencha os dados:
   - Tipo de Fonte (Playlist, Canal ou Documento)
   - URL ou ID da fonte
   - Tipo de Análise (FAQ, Copywriting ou Framework)
   - Idioma de saída
   - Idiomas preferidos (opcional)
4. Clique em "Iniciar Processamento"
5. Acompanhe o progresso no Dashboard

### Opção 2: API Direta (REST)

#### Criar um Job

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

#### Iniciar Processamento

```bash
curl -X POST "http://localhost:8000/api/processing/start/{job_id}"
```

#### Ver Progresso

```bash
curl "http://localhost:8000/api/jobs/{job_id}/progress"
```

#### Listar Resultados

```bash
curl "http://localhost:8000/api/results?job_id={job_id}"
```

### Opção 3: CLI Original (Mantido)

O CLI original ainda funciona:

```bash
python app.py
```

## 🐳 Docker (Opcional)

### Usar Docker Compose

```bash
# Inicia todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

Serviços disponíveis:
- API: http://localhost:8000
- Frontend: http://localhost:8501
- Redis: localhost:6379

## 📊 Fluxo Completo

### 1. Criar Job via Frontend
```
Frontend → API POST /api/jobs → Banco de Dados
```

### 2. Iniciar Processamento
```
Frontend → API POST /api/processing/start/{job_id} → Celery Worker
```

### 3. Worker Processa
```
Worker → Download Transcrição → Processamento IA → Salva Resultado → Atualiza DB
```

### 4. Acompanhar Progresso
```
Frontend → API GET /api/jobs/{id}/progress → Exibe no Dashboard
```

### 5. Ver Resultados
```
Frontend → API GET /api/results → Lista e Download
```

## 🔍 Endpoints da API

### Jobs
- `POST /api/jobs` - Criar job
- `GET /api/jobs` - Listar jobs
- `GET /api/jobs/{id}` - Detalhes do job
- `PATCH /api/jobs/{id}` - Atualizar job
- `DELETE /api/jobs/{id}` - Deletar job
- `GET /api/jobs/{id}/progress` - Progresso

### Processamento
- `POST /api/processing/start/{job_id}` - Iniciar processamento
- `POST /api/processing/cancel/{job_id}` - Cancelar processamento

### Vídeos
- `GET /api/videos` - Listar vídeos
- `GET /api/videos/{id}` - Detalhes do vídeo

### Resultados
- `GET /api/results` - Listar resultados
- `GET /api/results/{id}` - Detalhes do resultado
- `GET /api/results/{id}/download` - Download do arquivo

### WebSocket
- `WS /ws/jobs/{job_id}` - Progresso em tempo real

## 🛠️ Troubleshooting

### API não inicia
- Verifique se a porta 8000 está livre
- Confirme que o `.env` está configurado
- Execute `python scripts/init_db.py`

### Worker não processa
- Verifique se Redis está rodando
- Confirme variáveis de ambiente do Celery
- Veja logs do worker: `python scripts/start_worker.py`

### Frontend não conecta
- Verifique se a API está rodando
- Confirme a URL da API nas Configurações
- Teste: `curl http://localhost:8000/health`

### Erro de importação
- Certifique-se de estar no diretório raiz
- Execute: `pip install -r requirements.txt`
- Verifique o Python path

## 📚 Documentação Adicional

- [PRD](./PRD_FRONTEND.md) - Requisitos do produto
- [Arquitetura](./ARCHITECTURE.md) - Arquitetura do sistema
- [Status de Implementação](./IMPLEMENTATION_STATUS.md) - Progresso atual
- [README Frontend](../README_FRONTEND.md) - Guia do frontend

---

**Pronto para usar!** 🎉

