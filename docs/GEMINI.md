# Visão Geral do Projeto

Este projeto é uma ferramenta de linha de comando em Python para automatizar o download de transcrições de vídeos do YouTube e seu processamento através de um Modelo de Linguagem Grande (LLM), primariamente o Google Gemini. O sistema é projetado para ser robusto, com funcionalidades de fallback, retomada automática e múltiplos modos de análise.

## Fluxo de Trabalho

1.  **Entrada do Usuário**: O usuário executa `app.py` e, através de um menu interativo, seleciona o tipo de análise (ex: FAQ, Copywriting), o idioma de saída e a fonte dos vídeos (playlist do YouTube ou canal).
2.  **Coleta de Vídeos**: O sistema busca a lista de vídeos correspondente à fonte fornecida.
3.  **Download de Transcrições**: Para cada vídeo, o script tenta baixar a transcrição no idioma preferido. Se falhar, possui um sistema de fallback e novas tentativas. As transcrições brutas são salvas em `data/transcriptions/`.
4.  **Processamento com LLM**: Cada transcrição é enviada para a API do Gemini com um prompt customizável (localizado em `config/prompts/`) para realizar a análise definida (ex: extrair um FAQ).
5.  **Armazenamento Final**: O texto processado retornado pelo LLM é salvo em um novo arquivo no diretório `data/processed/`.
6.  **Gerenciamento de Progresso**: O sistema salva o progresso a cada vídeo, permitindo que tarefas interrompidas sejam retomadas do ponto onde pararam.

## Tecnologias Utilizadas

*   **Linguagem**: Python 3.7+
*   **APIs**:
    *   Google Gemini API
    *   YouTube Data API v3 (Opcional, para buscar vídeos de canais)
*   **Bibliotecas Principais**:
    *   `google-generativeai`: Para interagir com a API do Gemini.
    *   `youtube-transcript-api`: Para baixar as transcrições dos vídeos.
    *   `pytube`: Para obter metadados de playlists do YouTube.
    *   `python-dotenv`: Para gerenciar as variáveis de ambiente.
    *   `termcolor`: Para a interface colorida no terminal.

# Configuração e Execução

## 1. Instalação

Recomenda-se o uso de um ambiente virtual.

```bash
# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## 2. Variáveis de Ambiente

Crie um arquivo chamado `.env` na raiz do projeto (pode copiar de `.env.example`) e adicione as seguintes chaves:

```
# Chave de API do Google Gemini
API_KEY="SUA_CHAVE_DA_API_DO_GEMINI"

# Modelo do LLM a ser usado (opcional)
LLM_MODEL="gemini-2.5-flash" 

# Chave de API do YouTube (necessária para buscar vídeos de um canal)
YOUTUBE_API_KEY="SUA_CHAVE_DA_API_DO_YOUTUBE"
```

## 3. Prompts (Opcional)

Para personalizar a análise da IA, edite os arquivos de prompt localizados em `config/prompts/`.

## 4. Execução

Para iniciar a aplicação, execute o script principal e siga as instruções no terminal:

```bash
python3 app.py
```
O script guiará você na escolha do modo de análise, idioma, fonte dos vídeos e outras configurações.

# Estrutura de Diretórios

*   `app.py`: Ponto de entrada principal da aplicação.
*   `requirements.txt`: Lista de dependências Python.
*   `.env`: Arquivo para as variáveis de ambiente (não versionado).
*   `config/`: Contém os prompts para a IA.
*   `core/`: Contém a lógica de negócio principal.
    *   `sources.py`, `sources_playlist.py`, `sources_channel.py`: Módulos para buscar vídeos.
    *   `transcription.py`: Módulo para baixar as transcrições.
    *   `processing.py`: Módulo para processar as transcrições com o LLM.
    *   `progress.py`: Lida com o salvamento e a retomada do progresso.
*   `data/`: Armazena todos os dados de tempo de execução.
    *   `transcriptions/`: Armazena as transcrições brutas.
    *   `processed/`: Armazena os textos finais processados pelo LLM.
    *   `progress/`: Salva o estado atual para a funcionalidade de retomada.
*   `docs/`: Contém a documentação detalhada do projeto.
*   `logs/`: Armazena logs da aplicação, como falhas no download de transcrições.
