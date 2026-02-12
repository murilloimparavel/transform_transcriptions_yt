# 🚀 Guia de Configuração - YouTube Transcription Processor

Este guia irá ajudá-lo a configurar o projeto para rodar corretamente.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Chaves de API:
  - Google Gemini API Key
  - YouTube Data API v3 Key

## 🔧 Passo a Passo

### 1. Verificar Python

```bash
python --version
# Deve mostrar Python 3.8 ou superior
```

### 2. Criar Ambiente Virtual (Recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

#### Opção A: Usando o arquivo de exemplo

1. Copie o arquivo de exemplo:
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas chaves:
   ```env
   API_KEY=sua_chave_gemini_aqui
   YOUTUBE_API_KEY=sua_chave_youtube_aqui
   LLM_MODEL=gemini-2.5-flash
   USE_PROXIES=false
   PROXIES=
   ```

#### Opção B: Criar manualmente

Crie um arquivo `.env` na raiz do projeto (`transform_transcriptions_yt/.env`) com o seguinte conteúdo:

```env
# Google Gemini API Key
API_KEY=sua_chave_gemini_aqui

# YouTube Data API v3 Key
YOUTUBE_API_KEY=sua_chave_youtube_aqui

# Modelo do LLM (opcional)
LLM_MODEL=gemini-2.5-flash

# Usar proxies rotativos (opcional)
USE_PROXIES=false

# Lista de proxies customizados (opcional)
PROXIES=
```

### 5. Obter as Chaves API

#### Google Gemini API Key
1. Acesse: https://aistudio.google.com/app/api-keys
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada
5. Cole no arquivo `.env` como valor de `API_KEY`

#### YouTube Data API v3 Key
1. Acesse: https://console.cloud.google.com/apis/credentials
2. Faça login com sua conta Google
3. Crie um novo projeto ou selecione um existente
4. Ative a API "YouTube Data API v3"
5. Crie uma credencial do tipo "API Key"
6. Copie a chave gerada
7. Cole no arquivo `.env` como valor de `YOUTUBE_API_KEY`

### 6. Verificar Estrutura de Diretórios

O projeto criará automaticamente os diretórios necessários, mas você pode verificar se existem:

```
transform_transcriptions_yt/
├── data/
│   ├── transcriptions/    # Transcrições baixadas
│   ├── processed/         # Resultados processados
│   ├── playlists/         # Cache de playlists
│   ├── progress/          # Estado do progresso
│   └── proxies/           # Cache de proxies
├── logs/                  # Arquivos de log
└── config/
    └── prompts/           # Templates de prompts
```

### 7. Testar a Instalação

Execute o script de verificação:

```bash
python setup.py
```

Ou teste diretamente:

```bash
python app.py
```

## ✅ Verificação Rápida

Execute estes comandos para verificar se tudo está configurado:

```bash
# Verificar Python
python --version

# Verificar dependências principais
python -c "import google.generativeai; print('✓ google-generativeai')"
python -c "import dotenv; print('✓ python-dotenv')"
python -c "import pytube; print('✓ pytube')"
python -c "from youtube_transcript_api import YouTubeTranscriptApi; print('✓ youtube-transcript-api')"

# Verificar arquivo .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ .env carregado'); print('API_KEY:', '✓ configurada' if os.getenv('API_KEY') and os.getenv('API_KEY') != 'sua_chave_gemini_aqui' else '✗ não configurada')"
```

## 🐛 Problemas Comuns

### Erro: "ModuleNotFoundError"
**Solução:** Instale as dependências:
```bash
pip install -r requirements.txt
```

### Erro: "API_KEY not found"
**Solução:** Verifique se o arquivo `.env` existe e contém a variável `API_KEY` com uma chave válida.

### Erro: "YOUTUBE_API_KEY not found"
**Solução:** Verifique se o arquivo `.env` existe e contém a variável `YOUTUBE_API_KEY` com uma chave válida.

### Erro ao importar módulos
**Solução:** Certifique-se de estar na pasta correta:
```bash
cd transform_transcriptions_yt
python app.py
```

## 📝 Próximos Passos

Após a configuração, você pode:

1. Executar o projeto:
   ```bash
   python app.py
   ```

2. Seguir o fluxo interativo:
   - Escolher tipo de análise (FAQ, Copywriting ou Framework)
   - Selecionar idioma de saída
   - Escolher fonte (Playlist ou Canal)
   - Aguardar processamento

3. Verificar resultados em `data/processed/`

## 🔗 Links Úteis

- [Documentação do Google Gemini](https://ai.google.dev/docs)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Documentação do Projeto](./docs/README.md)

---

**Pronto para usar! 🎉**

