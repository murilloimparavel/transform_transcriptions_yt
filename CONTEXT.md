# YouTube Transcription Processor - Contexto Completo do Sistema

## Visão Geral

O **YouTube Transcription Processor** é um sistema automatizado para transformar conteúdo não-estruturado (vídeos do YouTube e documentos) em conhecimento estruturado e acionável usando inteligência artificial (Google Gemini).

---

## O Que o Sistema Faz

1. **Extrai conteúdo** de playlists, canais ou vídeos individuais do YouTube
2. **Baixa transcrições** automaticamente com suporte multi-idioma
3. **Processa com IA** (Google Gemini) em 3 modos de análise
4. **Gera outputs estruturados**: FAQ, análises de copywriting ou frameworks completos
5. **Suporta documentos**: sites, PDFs, Word, Excel, CSV
6. **Contorna bloqueios** de IP usando sistema de proxies rotativos

---

## Estrutura de Diretórios

```
transform_transcriptions_yt/
├── app.py                          # Entry point principal (CLI)
├── check_setup.py                  # Verificação de setup
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de configuração
│
├── core/                           # Módulos principais
│   ├── __init__.py                 # Exportações
│   ├── transcription.py            # Download de transcrições
│   ├── processing.py               # Processamento com Gemini
│   ├── progress.py                 # Gerenciamento de progresso
│   ├── proxy_manager.py            # Proxies rotativos
│   ├── framework_processor.py      # Framework 7 dimensões
│   ├── agent_builder_processor.py  # Base conhecimento para agentes IA
│   ├── agent_consolidator.py       # Consolidação multi-arquivo para RAG
│   ├── document_extractor.py       # Extração de documentos
│   ├── faq_to_excel.py             # Conversão FAQ → Excel
│   ├── sources.py                  # Agregador de fontes
│   ├── sources_playlist.py         # Extrator de playlists
│   └── sources_channel.py          # Extrator de canais
│
├── config/prompts/                 # Templates de prompts IA
│   ├── faq.txt                     # Prompt FAQ
│   ├── copywriting.txt             # Prompt copywriting
│   ├── prompt_framework.txt        # Prompt framework completo
│   └── agent_builder.txt           # Prompt Agent Builder (base IA)
│
├── data/                           # Dados e cache
│   ├── transcriptions/             # Transcrições baixadas
│   ├── processed/                  # Resultados processados
│   ├── playlists/                  # Cache de playlists
│   ├── progress/                   # Estado de progresso
│   └── proxies/                    # Cache de proxies
│
├── logs/                           # Arquivos de log
│   └── transcriptions.log
│
└── docs/                           # Documentação adicional
```

---

## Bibliotecas e Dependências

### Principais

| Biblioteca | Versão | Propósito |
|-----------|--------|-----------|
| `google-generativeai` | 0.8.5 | API Google Gemini (IA) |
| `google-api-python-client` | 2.172.0 | YouTube Data API |
| `youtube-transcript-api` | 1.2.3 | Download de transcrições |
| `pytube` | 15.0.0 | Metadados de vídeos |
| `python-dotenv` | 1.1.0 | Variáveis de ambiente |
| `requests` | 2.31.0 | Requisições HTTP |
| `beautifulsoup4` | 4.12.2 | Web scraping |
| `PyPDF2` | 3.0.1 | Extração de PDFs |
| `python-docx` | 1.1.0 | Extração de Word |
| `openpyxl` | 3.1.2 | Criação de Excel |
| `xlrd` | 2.0.1 | Leitura Excel legado |
| `lxml` | 4.9.3 | Parser XML/HTML |
| `termcolor` | 3.1.0 | Output colorido |

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface (app.py)                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Menu de Configuração Interativo             │    │
│  │  - Tipo de análise (FAQ/Copywriting/Framework)          │    │
│  │  - Idioma de saída (PT/EN)                              │    │
│  │  - Fonte (Playlist/Canal/Vídeo/Documentos)              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  sources_*.py     │ │ document_       │ │  progress.py    │
│  (Extrai URLs)    │ │ extractor.py    │ │  (Rastreia      │
│                   │ │ (Extrai texto)  │ │   estado)       │
└─────────┬─────────┘ └────────┬────────┘ └────────┬────────┘
          │                    │                   │
          ▼                    ▼                   │
┌─────────────────────────────────────────────────┤
│              transcription.py                    │
│  (Download com retry e fallback)                 │
│  ┌─────────────────────────────────────────┐    │
│  │         proxy_manager.py                 │    │
│  │  (Proxies rotativos + cache)            │    │
│  └─────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│           processing.py / framework_processor.py                 │
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │ config/prompts/ │───▶│      Google Gemini API           │   │
│  │ (Templates IA)  │    │  (Análise e estruturação)        │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output Generators                           │
│  ┌────────────────────┐    ┌────────────────────────────────┐  │
│  │  faq_to_excel.py   │    │  data/processed/               │  │
│  │  (Gera .xlsx)      │    │  (Arquivos .txt estruturados)  │  │
│  └────────────────────┘    └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Modos de Análise

### 1. Modo FAQ
Extrai perguntas e respostas estruturadas com:
- Pergunta principal e variações
- Resposta estruturada (120-220 palavras)
- Framework mental (princípios, pilares, aplicação)
- Modelos mentais (percepções, heurísticas)
- Tags e categorização automática
- **Saída**: TXT + Excel formatado

### 2. Modo Copywriting
Extrai frameworks de vendas high ticket:
- Resumo estratégico
- Framework sequencial de copy
- Checklist de execução
- Erros comuns a evitar
- **Saída**: TXT estruturado

### 3. Modo Framework Completo (7 Dimensões)
Extração profunda e multidimensional:
1. Framework de implementação
2. Insights revolucionários
3. Aspectos contra-intuitivos
4. Histórias transformadoras
5. Números e fórmulas exatas
6. Aplicações imediatas (2h/1sem/1mês)
7. Citações e mantras
- **Saída**: TXT com 7 seções

### 4. Modo Agent Builder (Base de Conhecimento para IA)
Preparação otimizada de conteúdo para treinar agentes de IA:
1. Ontologia do domínio (glossário, hierarquia, relações)
2. Base de conhecimento factual (fatos, números, fórmulas)
3. Procedimentos e instruções (processos, árvores de decisão)
4. Exemplos e casos (histórias, comparações)
5. Perguntas e respostas (Q&A para RAG)
6. Contexto e metadados (resumo, mapa de tópicos)
7. Instruções para o agente (persona, regras)
- **Saída**: TXT legível + JSON estruturado para integração RAG

#### Consolidação Automática (Agent Builder)
Após processar múltiplos vídeos, o sistema automaticamente:
1. Extrai Q&As de todos os JSONs
2. Consolida em uma mega planilha Excel
3. Gera System Prompt unificado
4. Organiza tudo em pastas estruturadas

**Estrutura de saída**:
```
data/processed/agent_consolidado_[projeto]/
├── mega_planilha/           # Excel com abas: Q&A, Fatos, Procedimentos, Glossário, Exemplos
├── system_prompt/           # Prompt consolidado para o agente
├── json/                    # JSONs originais de cada vídeo
└── txt/                     # TXTs originais de cada vídeo
```

---

## Configuração

### Variáveis de Ambiente (.env)

```env
# OBRIGATÓRIO
API_KEY=sua_chave_gemini_aqui
LLM_MODEL=gemini-1.5-flash-002
YOUTUBE_API_KEY=sua_chave_youtube_aqui

# OPCIONAL - Sistema de Proxies
USE_PROXIES=false
# PROXIES=http://1.2.3.4:8080,http://5.6.7.8:3128
# PREMIUM_PROXY_URL=http://user:pass@proxy.com:8080
```

### Instalação

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com suas chaves de API

# 3. Verificar setup
python check_setup.py
```

---

## Como Usar

### Execução Básica

```bash
python app.py
```

### Fluxo de Menu

1. **Detecta tarefa incompleta** → Opção de continuar ou reiniciar
2. **Escolher tipo de análise**: FAQ / Copywriting / Framework
3. **Escolher idioma de saída**: Português / Inglês
4. **Configurar idiomas de legenda**: ex: `pt,en`
5. **Escolher fonte**:
   - Playlist do YouTube
   - Canal do YouTube
   - Vídeo(s) individual(is)
   - Documentos (URL, PDF, Word, Excel, CSV)

---

## Fluxos de Dados

### Fluxo de Vídeos

```
URL Playlist/Canal
    ↓
Extração de URLs de vídeos
    ↓
Para cada vídeo:
    ├── Download transcrição (com proxy/fallback)
    ├── Salvamento em data/transcriptions/
    ├── Processamento com Gemini
    └── Resultado em data/processed/
    ↓
Pós-processamento (FAQ → Excel)
```

### Fluxo de Documentos

```
URL ou Arquivo Local
    ↓
Extração de texto
    ↓
Salvamento em data/transcriptions/documents/
    ↓
Processamento com Gemini
    ↓
Resultado em data/processed/documents/
```

---

## Sistema de Progresso

O sistema salva automaticamente o estado em `data/progress/progress.json`:
- Vídeos já processados
- Índice atual
- Estatísticas de execução

**Permite retomar tarefas interrompidas automaticamente.**

---

## Sistema de Proxies

### Funcionamento

1. Tenta download direto
2. Se bloqueado → ativa proxy do cache
3. Se proxy falha → rotaciona para próximo
4. Fallback final → Kome.ai API

### Fontes de Proxies

1. Cache local (`good_proxies.json`)
2. Free Proxy List (BR)
3. Proxifly (global)
4. ProxyScrape (global)

---

## Integrações Externas

| Serviço | Propósito | Autenticação |
|---------|-----------|--------------|
| Google Gemini | Processamento IA | API Key |
| YouTube Data API | Metadados de canais | API Key |
| YouTube Transcript API | Download transcrições | Sem auth |
| Kome.ai | Fallback transcrições | Sem auth |
| Free Proxy Lists | Proxies rotativos | Sem auth |

---

## Limitações Conhecidas

- **Limite Gemini**: 250 req/dia (plano gratuito)
- **Bloqueio YouTube**: Sem proxies premium, pode bloquear IP
- **Transcrições**: Apenas vídeos com legendas habilitadas
- **Rate Limiting**: Aguarda 60s após limite atingido

---

## Estrutura de Saída FAQ

```
q: Pergunta principal aqui?
sq: variação1 | variação2 | variação3
a: Resposta estruturada com 120-220 palavras...
f:
- Princípio central
- Pilares/componentes
- Aplicação prática
- Exemplo/história
m:
- Percepção chave
- Heurísticas mentais
- Critérios de decisão
tags: tag1, tag2, tag3
categoria: Concept|Principle|Procedure|Example|Strategy
---
```

---

## Logs e Debug

- **Console**: WARNING e ERROR apenas
- **Arquivo**: `logs/transcriptions.log` (INFO+)

---

## Arquivos Principais

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `app.py` | ~1050 | CLI principal, coordenação |
| `core/transcription.py` | ~347 | Download com retry |
| `core/processing.py` | ~166 | Processamento Gemini |
| `core/proxy_manager.py` | ~400 | Sistema de proxies |
| `core/progress.py` | ~200 | Gerenciamento de estado |
| `core/framework_processor.py` | ~300 | Framework 7 dimensões |
| `core/agent_builder_processor.py` | ~280 | Base de conhecimento para agentes IA |
| `core/agent_consolidator.py` | ~550 | Consolidação multi-arquivo para RAG |
| `core/document_extractor.py` | ~250 | Extração multi-formato |
| `core/faq_to_excel.py` | ~200 | Conversão FAQ → Excel |

---

## Casos de Uso

1. **Criar base de FAQ** de cursos/webinars
2. **Extrair frameworks** de metodologias de vendas
3. **Consolidar conhecimento** de múltiplos canais
4. **Gerar documentação** estruturada de palestras
5. **Analisar concorrência** via conteúdo público
6. **Treinar agentes de IA** especialistas em qualquer assunto (Agent Builder)

---

## Comandos Úteis

```bash
# Executar sistema
python app.py

# Verificar setup
python check_setup.py

# Ver logs
tail -f logs/transcriptions.log  # Linux/Mac
Get-Content logs/transcriptions.log -Wait  # PowerShell
```

---

*Última atualização: Janeiro 2026*
