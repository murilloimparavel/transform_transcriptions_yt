# 🎬 YouTube Transcription Processor

Sistema automatizado para download e processamento de transcrições do YouTube com IA, incluindo suporte a proxies rotativos e análise avançada de conteúdo.

## ✨ Características

- 📥 **Download automático** de transcrições de vídeos, playlists e canais
- 🌍 **Multi-idioma** com detecção automática de legendas disponíveis
- 🔄 **Sistema de proxies** rotativos para evitar bloqueio de IP
- 🤖 **Processamento com IA** usando Google Gemini
- 📊 **3 modos de análise**: FAQ, Copywriting e Framework Completo
- 💾 **Sistema de progresso** com retomada automática
- 🧹 **Logs limpos** com níveis separados (console/arquivo)

## 🚀 Instalação

```bash
# Clone o repositório
git clone [URL_DO_REPOSITORIO]
cd "Tratamento de dados"

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

2. Edite `.env` e adicione suas chaves:
```env
API_KEY=sua_chave_gemini_aqui
YOUTUBE_API_KEY=sua_chave_youtube_aqui
LLM_MODEL=gemini-2.5-flash
USE_PROXIES=false
```

### Como Obter as Chaves API

- **Google Gemini**: https://aistudio.google.com/app/api-keys
- **YouTube Data API**: https://console.cloud.google.com/apis/credentials

## 📖 Uso

```bash
python3 app.py
```

### Fluxo de Uso

1. **Escolha o tipo de análise**:
   - FAQ - Extração de conhecimento estruturado
   - Copywriting - Frameworks de vendas
   - Framework Completo - Análise profunda em 7 dimensões

2. **Configure idiomas**:
   - Idioma de saída da IA (pt/en)
   - Idiomas preferidos para legendas (pt,en ou vazio)

3. **Selecione a fonte**:
   - Playlist do YouTube
   - Canal do YouTube

4. **Aguarde o processamento**:
   - Downloads automáticos
   - Processamento com IA
   - Resultados em `data/processed/`

## 📁 Estrutura do Projeto

```
.
├── app.py                  # Aplicação principal
├── core/                   # Módulos principais
│   ├── __init__.py
│   ├── transcription.py    # Download de transcrições
│   ├── processing.py       # Processamento com IA
│   ├── proxy_manager.py    # Gerenciamento de proxies
│   ├── progress.py         # Sistema de progresso
│   └── framework_processor.py
├── config/
│   └── prompts/           # Templates de prompts
├── data/
│   ├── transcriptions/    # Transcrições baixadas
│   ├── processed/         # Resultados processados
│   ├── playlists/         # Cache de playlists
│   ├── progress/          # Estado do progresso
│   └── proxies/           # Cache de proxies
├── logs/                  # Arquivos de log
├── docs/                  # Documentação
├── .env                   # Configurações (não versionado)
└── requirements.txt       # Dependências
```

## 🔧 Funcionalidades Avançadas

### Sistema de Proxies

O projeto inclui sistema avançado de proxies rotativos:

- ✅ Validação específica contra YouTube
- ✅ Teste em massa paralelo (26x mais rápido)
- ✅ Rotação automática quando bloqueado
- ✅ Cache VIP com proxies validados (24h)
- ✅ Fallback automático para Kome.ai

Para ativar:
```env
USE_PROXIES=true
```

Consulte `docs/PROXY_SYSTEM.md` para detalhes.

### Sistema de Progresso

- ✅ Retoma automaticamente de onde parou
- ✅ Salva estado a cada vídeo processado
- ✅ Detecta tarefas incompletas ao iniciar
- ✅ Permite continuar ou reiniciar

### Modos de Análise

1. **FAQ**: Extrai perguntas e respostas estruturadas
2. **Copywriting**: Identifica frameworks de vendas e gatilhos
3. **Framework**: Análise profunda em 7 dimensões + síntese

## 📊 Limites e Quotas

### Google Gemini (Plano Gratuito)
- **250 requisições/dia** para gemini-2.5-flash
- Sistema implementa retry automático com rate limiting

Para produção, considere:
- Upgrade para plano pago do Gemini
- Uso de proxies premium para maior volume

## 🐛 Troubleshooting

### Erro 429 (Quota Exceeded)
```
⚠️  Quota da API excedida!
⏳ Aguardando 45 segundos...
```
**Solução**: Sistema aguarda automaticamente. Para evitar, use modelo com quota maior.

### Bloqueio de IP pelo YouTube
```
WARNING: [video_id] IP bloqueado pelo YouTube
```
**Solução**: 
1. Ative proxies: `USE_PROXIES=true` no `.env`
2. Sistema rotaciona automaticamente
3. Fallback para Kome.ai se necessário

### Vídeo sem legendas
```
WARNING: [video_id] Legendas desabilitadas
```
**Solução**: Sistema pula automaticamente para próximo vídeo.

## 📚 Documentação

- `docs/PROXY_SYSTEM.md` - Sistema de proxies completo
- `docs/PROXY_IMPROVEMENTS.md` - Melhorias implementadas
- `docs/LOGS_LIMPOS.md` - Sistema de logs
- `docs/BARRA_PROGRESSO.md` - Barra de progresso
- `RESUMO_FINAL.md` - Resumo técnico completo

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - API de transcrições
- [pytube](https://github.com/pytube/pytube) - Download de vídeos
- [Google Gemini](https://ai.google.dev/) - Processamento com IA
- [Proxifly](https://github.com/proxifly/free-proxy-list) - Lista de proxies gratuitos

## 📞 Suporte

Para bugs e sugestões, abra uma [issue](../../issues) no GitHub.

---

**Desenvolvido com ❤️ para processamento automatizado de conteúdo do YouTube**
