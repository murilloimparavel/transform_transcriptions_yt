# YouTube Transcription Processor

Sistema automatizado para download, processamento e transformacao de transcricoes do YouTube (e documentos) em bases de conhecimento estruturadas usando Google Gemini. Suporta proxies rotativos, multiplos modos de analise com IA e consolidacao para treinamento de agentes.

## Funcionalidades Principais

- **5 fontes de conteudo**: Playlists, canais, videos individuais, documentos (URL/PDF/Word/Excel/CSV/TXT/Markdown) e consolidacao de outputs existentes
- **4 modos de analise com IA**: FAQ, Copywriting, Framework Completo (7 dimensoes) e Agent Builder (RAG-ready)
- **Transcricao dual-source**: YouTube Transcript API com fallback automatico para Kome.ai
- **Proxy system**: Rotacao automatica com validacao em massa, lista VIP persistente e fallback
- **Progresso persistente**: Retomada automatica de tarefas interrompidas
- **Multi-idioma**: Legendas em qualquer idioma + output em PT-BR ou EN
- **Consolidacao para agentes**: Gera planilha Excel, system prompt e JSON consolidado a partir de multiplos videos

---

## Instalacao

### Setup Automatico (Recomendado)

```bash
cd transform_transcriptions_yt
python setup.py
```

O script verifica Python, instala dependencias, cria diretorios e gera o `.env`.

### Instalacao Manual

```bash
# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Instale dependencias
pip install -r requirements.txt

# Configure variaveis de ambiente
copy env.example .env        # Windows
cp env.example .env          # Linux/Mac
```

### Configuracao do .env

```env
API_KEY=sua_chave_gemini_aqui
YOUTUBE_API_KEY=sua_chave_youtube_aqui
LLM_MODEL=gemini-2.5-flash
USE_PROXIES=false
```

**Como obter as chaves:**
- Google Gemini: https://aistudio.google.com/app/api-keys
- YouTube Data API v3: https://console.cloud.google.com/apis/credentials

**Verificar configuracao:**
```bash
python check_setup.py
```

---

## Uso

```bash
python app.py
```

O menu interativo guia pelas etapas:

### 1. Escolha do modo de analise

| Modo | Descricao | Output |
|------|-----------|--------|
| **FAQ** | Extrai conhecimento em Q&A estruturado para RAG. Cada item tem pergunta, variacoes, resposta, framework, tags e categoria. | `.txt` + `.xlsx` |
| **Copywriting** | Extrai frameworks de vendas high-ticket em 4 blocos: resumo estrategico, framework de copy, checklist e erros comuns. | `.txt` |
| **Framework Completo** | Analise profunda multi-stage em 7 dimensoes (implementacao, insights, contra-intuitivos, historias, numeros, aplicacoes, citacoes) + sintese final. | `.txt` + `.json` |
| **Agent Builder** | Gera base de conhecimento completa para agentes IA em 7 blocos (ontologia, fatos, procedimentos, exemplos, Q&A, contexto, instrucoes do agente). Otimizado para RAG. | `.txt` + `.json` |

### 2. Configuracao de idioma

- **Idioma de saida da IA**: Portugues (pt) ou Ingles (en)
- **Idiomas de legenda preferidos**: Lista de prioridade (ex: `pt,en`) ou vazio para qualquer

### 3. Selecao da fonte

| Fonte | Descricao |
|-------|-----------|
| **Playlist** | Processa todos os videos de uma playlist do YouTube |
| **Canal** | Busca todos os videos de um canal (filtra Shorts < 60s, ordena por duracao) |
| **Video(s)** | 1 a 10 URLs de videos individuais separados por virgula |
| **Documentos** | URL de site, PDF, Word (.docx), Texto (.txt), Markdown (.md), Excel (.xlsx/.xls) ou CSV. Ate 10 fontes separadas por virgula |
| **Consolidar Agent Builder** | Consolida arquivos Agent Builder ja processados em estrutura unificada |

---

## Modos de Analise em Detalhe

### FAQ

Transforma conteudo em Q&A estruturado seguindo formato especifico:
- `q:` pergunta principal
- `sq:` variacoes da pergunta
- `a:` resposta em 1a pessoa no tom do autor (120-220 palavras)
- `f:` framework com principio central, pilares, aplicacao pratica, exemplos, metricas e armadilhas
- `tags:` 3-7 palavras-chave
- `categoria:` Concept, Principle, Procedure, Example, Story, Quote, Strategy, Metric, Warning, Checklist, Decision, Framework ou Exercise

Para documentos, gera automaticamente planilha Excel com categorizacao inteligente por palavras-chave. Suporta consolidacao de FAQs de multiplas fontes em uma unica planilha.

### Copywriting

Focado em vendas high-ticket. Extrai:
- **Bloco 1** - Resumo Estrategico: problema central, grande sacada, diferencial
- **Bloco 2** - Framework de Copy: etapas do anuncio (Gancho -> Credibilidade -> Oferta -> CTA), exemplos e gatilhos mentais
- **Bloco 3** - Checklist de Execucao: verificacao de gancho, prova social, valor percebido, CTA
- **Bloco 4** - Erros Comuns: armadilhas e o que evitar

Rejeita conteudos que nao sao sobre copywriting high-ticket.

### Framework Completo

Processamento multi-stage (7 chamadas ao Gemini + sintese). Cada dimensao e processada separadamente para lidar com limites de contexto:

1. **Framework de Implementacao**: arquitetura conceitual, processo sequencial, arvore de decisao, metricas
2. **Insights Revolucionarios**: 5-10 insights com exemplos e impacto pratico
3. **Aspectos Contra-Intuitivos**: 10-15 paradoxos com evidencia
4. **Historias e Casos**: sucesso, fracasso, historia pessoal do autor
5. **Numeros e Formulas**: metricas, benchmarks, timeframes
6. **Aplicacoes Imediatas**: acoes para 2h, esta semana e este mes
7. **Citacoes e Mantras**: frases-chave e perguntas poderosas

Finaliza com sintese integradora e plano 30-60-90 dias.

### Agent Builder

Modo recomendado. Gera base de conhecimento completa para treinar agentes IA, otimizada para RAG:

1. **Ontologia do Dominio**: glossario, hierarquia de conceitos, relacoes
2. **Base Factual**: fatos, afirmacoes, numeros, metricas, formulas
3. **Procedimentos**: processos passo a passo, arvores de decisao, checklists
4. **Exemplos e Casos**: casos de estudo completos com contexto, intervencao e resultado
5. **Perguntas e Respostas**: Q&A implicitos extraidos + objecoes com respostas
6. **Contexto e Metadados**: info da fonte, resumo executivo, mapa de topicos
7. **Instrucoes para o Agente**: persona, regras de engajamento, conexoes entre blocos

Formato YAML-like com IDs unicos para referencia cruzada. Output em TXT (leitura humana) e JSON (integracao programatica).

---

## Consolidacao de Agent Builder

Apos processar multiplos videos/documentos no modo Agent Builder, o consolidador combina tudo em uma estrutura unificada:

```
data/processed/agent_consolidado_<nome_projeto>/
├── mega_planilha/          # Excel com 6 abas (Q&A, Fatos, Procedimentos, Glossario, Exemplos, Metadados)
├── system_prompt/          # System Prompt consolidado para o agente
├── json/                   # JSONs originais de cada video
├── txt/                    # TXTs originais de cada video
└── consolidated_data.json  # JSON com todos os dados unificados
```

A mega planilha contem:
- **Q&A**: Pergunta, resposta, fonte e tags (principal para RAG)
- **Fatos**: Afirmacoes fatuais com tipo e fonte
- **Procedimentos**: Processos com passos detalhados
- **Glossario**: Termos tecnicos com definicoes
- **Exemplos**: Casos de estudo documentados
- **Metadados**: Estatisticas e lista de fontes

O system prompt consolidado inclui persona do agente, estatisticas da base, regras de resposta e instrucoes por fonte.

---

## Sistema de Transcricao

### Fluxo de Download

1. Tenta **YouTube Transcript API** com idiomas preferidos do usuario
2. Se nao encontrar no idioma preferido, pega qualquer legenda disponivel (manual > automatica)
3. Se IP bloqueado e proxies ativos: rotaciona proxy e retenta
4. Se YouTube falhar completamente: usa **Kome.ai** como fallback
5. Salva transcricao em `data/transcriptions/<video_id>_<idioma>.txt`
6. Pula videos que ja tem transcricao baixada

### Rate Limiting

- 5s entre downloads de transcricoes
- 30s entre processamentos de videos
- 60s de espera automatica em erro 429 (quota excedida)
- 20s entre dimensoes/blocos no Framework e Agent Builder

---

## Sistema de Proxies

Ativado via `USE_PROXIES=true` no `.env`. Recursos:

- **Fontes automaticas**: Proxifly (HTTP + HTTPS global), ProxyScrape, proxies BR dedicados
- **Validacao em massa**: ThreadPoolExecutor com ate 30 threads, testando contra youtube.com
- **Lista VIP persistente**: Proxies que funcionaram sao salvos em `data/proxies/good_proxies.json` (validos por 24h)
- **Blacklist temporaria**: Proxies falhos sao bloqueados por 1h em `data/proxies/bad_proxies.json`
- **Rotacao automatica**: Quando IP e bloqueado, troca de proxy sem interromper processamento
- **Fallback**: Se todos os proxies falharem, muda automaticamente para Kome.ai

---

## Sistema de Progresso

- Salva estado em `data/progress/progress.json` a cada video processado
- Ao iniciar, detecta tarefas incompletas e oferece opcao de continuar ou reiniciar
- Registra: fonte, idiomas, tipo de prompt, indice atual e lista de videos
- Suporta interrupcao por Ctrl+C com retomada posterior

---

## Processamento de Documentos

Extrai texto de multiplos formatos e processa com os modos FAQ, Framework ou Agent Builder:

| Formato | Biblioteca | Detalhes |
|---------|-----------|----------|
| URL (sites) | BeautifulSoup | Web scraping, remove scripts/nav/footer |
| PDF (.pdf) | PyPDF2 | Extrai todas as paginas |
| Word (.docx) | python-docx | Paragrafos + tabelas |
| Texto (.txt) | built-in | Multi-encoding (UTF-8, Latin-1, CP1252) |
| Markdown (.md) | built-in | Multi-encoding |
| Excel (.xlsx) | openpyxl | Todas as planilhas, linhas formatadas com pipe |
| Excel (.xls) | xlrd | Formato legado |
| CSV (.csv) | csv | Auto-deteccao de delimitador e encoding |

Para FAQ com multiplos documentos, oferece opcao de consolidar todos os FAQs em uma unica planilha Excel.

---

## Estrutura do Projeto

```
.
├── app.py                          # Aplicacao principal (menu interativo + orquestracao)
├── core/
│   ├── __init__.py                 # Exports do modulo
│   ├── transcription.py            # Download de transcricoes (YouTube API + Kome.ai)
│   ├── processing.py               # Processamento com Gemini (FAQ/Copywriting por chunks)
│   ├── framework_processor.py      # Modo Framework Completo (7 dimensoes multi-stage)
│   ├── agent_builder_processor.py  # Modo Agent Builder (7 blocos para RAG)
│   ├── agent_consolidator.py       # Consolidacao de multiplos Agent Builder outputs
│   ├── document_extractor.py       # Extracao de texto de URL/PDF/Word/Excel/CSV/TXT/MD
│   ├── faq_to_excel.py             # Conversao de FAQ para Excel com categorizacao
│   ├── progress.py                 # Gerenciamento de progresso persistente
│   ├── proxy_manager.py            # Sistema de proxies rotativos
│   ├── sources.py                  # Re-export de sources_playlist e sources_channel
│   ├── sources_playlist.py         # Extracao de URLs de playlists (pytube)
│   └── sources_channel.py          # Listagem de videos de canais (YouTube Data API v3)
├── config/
│   └── prompts/
│       ├── faq.txt                 # Prompt para modo FAQ
│       ├── copywriting.txt         # Prompt para modo Copywriting
│       ├── prompt_framework.txt    # Prompt para modo Framework Completo
│       └── agent_builder.txt       # Prompt para modo Agent Builder
├── data/
│   ├── transcriptions/             # Transcricoes baixadas (por video ID)
│   │   └── documents/              # Textos extraidos de documentos
│   ├── processed/                  # Resultados processados pela IA
│   │   ├── documents/              # Documentos processados (FAQ Excel, etc.)
│   │   └── agent_consolidado_*/    # Projetos consolidados do Agent Builder
│   ├── playlists/                  # Cache de JSONs de playlists/canais
│   ├── progress/                   # Estado de progresso (progress.json)
│   └── proxies/                    # Listas de proxies (good/bad)
├── logs/                           # Logs detalhados (transcriptions.log)
├── docs/                           # Documentacao adicional
├── .env                            # Chaves de API e configuracoes (nao versionado)
├── .env.example                    # Exemplo de configuracao
├── requirements.txt                # Dependencias Python
├── setup.py                        # Script de setup automatico
├── check_setup.py                  # Verificacao de configuracao
├── list_models.py                  # Listagem de modelos Gemini disponiveis
├── test_model.py                   # Teste de conexao com Gemini
├── fix_env.py                      # Correcao de problemas no .env
└── LICENSE                         # MIT License
```

---

## Dependencias

| Pacote | Uso |
|--------|-----|
| `google-generativeai` | API do Google Gemini (LLM) |
| `google-api-python-client` | YouTube Data API v3 (canais) |
| `youtube-transcript-api` | Download de transcricoes do YouTube |
| `pytube` | Extracao de URLs de playlists |
| `requests` | HTTP requests (Kome.ai, proxies) |
| `beautifulsoup4` + `lxml` | Web scraping de sites |
| `PyPDF2` | Extracao de texto de PDFs |
| `python-docx` | Leitura de documentos Word |
| `openpyxl` | Leitura/escrita de Excel .xlsx |
| `xlrd` | Leitura de Excel .xls (legado) |
| `python-dotenv` | Gerenciamento de variaveis .env |
| `termcolor` | Output colorido no terminal |
| `isodate` | Parse de duracao ISO 8601 (filtro de Shorts) |

---

## Troubleshooting

### Erro 429 (Quota Exceeded)
O sistema aguarda 60 segundos automaticamente e retenta. Para evitar, use um modelo com quota maior ou plano pago do Gemini.

### IP bloqueado pelo YouTube
Ative proxies com `USE_PROXIES=true` no `.env`. O sistema rotaciona proxies e usa Kome.ai como fallback.

### Video sem legendas
O sistema pula automaticamente e continua com o proximo video. Verifique se o video possui legendas habilitadas.

### Timeout na API
Retry automatico com ate 3 tentativas e 5s de espera entre elas.

---

## Licenca

MIT License - Copyright (c) 2025 Murillo Alves. Veja [LICENSE](./LICENSE).
