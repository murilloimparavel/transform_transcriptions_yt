# 🎯 Novas Funcionalidades - Sistema Inteligente

## 📋 Resumo das Melhorias

### 1. **Auto-Detecção de Legendas** 🔍
- Sistema detecta automaticamente legendas disponíveis
- Permite especificar idiomas preferidos em ordem de prioridade
- Aceita qualquer legenda disponível se preferidas não existirem

### 2. **Seleção de Prompt** 📝
- Escolha entre 2 tipos de análise:
  - **FAQ**: Extração de conhecimento estruturado
  - **Copywriting**: Frameworks de vendas high ticket

### 3. **Idioma de Saída Configurável** 🌍
- Escolha o idioma do output final da IA
- Português (pt) ou Inglês (en)
- Independente do idioma das legendas

## 🚀 Como Funciona Agora

### Fluxo Completo de Uso

```
1. Execute: python3 app.py

2. CONFIGURAÇÃO DO PROCESSAMENTO
   ================================

   📝 Tipo de análise:
   [1] FAQ - Extração de conhecimento estruturado
   [2] Copywriting - Frameworks de vendas high ticket
   → Escolha: 2

   🌍 Idioma de saída da IA:
   [1] Português (pt)
   [2] Inglês (en)
   → Escolha: 1

   📺 Idiomas preferidos para legendas:
   Exemplos: 'pt,en' ou 'en,pt' ou 'pt'
   → Digite: pt,en

   ✓ Configurações salvas:
     - Tipo de análise: COPYWRITING
     - Idioma de saída: PT
     - Idiomas de legenda: ['pt', 'en']

3. FONTE DOS VÍDEOS
   [1] Playlist
   [2] Canal
   → Escolha e prossiga normalmente
```

## 📊 Detalhes Técnicos

### 1. Auto-Detecção de Legendas

**Antes:**
```python
# Fixo em um idioma
language = "pt"
```

**Agora:**
```python
# Lista de prioridades
preferred_languages = ['pt', 'en']  # Tenta pt primeiro, depois en
# ou
preferred_languages = None  # Aceita qualquer legenda disponível
```

**Lógica:**
1. Tenta encontrar legenda em `pt`
2. Se não existe, tenta `en`
3. Se não existe, pega a primeira disponível
4. Se nenhuma existe, marca como falha

**Logs:**
```
[video_id] Legenda encontrada no idioma preferido: pt
[video_id] Usando primeira legenda disponível: es
```

### 2. Sistema de Prompts

**Arquivos de Prompt:**
- `src/prompt.txt` → Copywriting (vendas high ticket)
- `src/prompt_faq.txt` → FAQ (extração de conhecimento)

**Carregamento Dinâmico:**
```python
def load_prompt(prompt_type="copywriting", output_language="pt"):
    # Seleciona arquivo baseado no tipo
    if prompt_type == "faq":
        prompt_path = 'src/prompt_faq.txt'
    else:
        prompt_path = 'src/prompt.txt'

    # Adiciona instrução de idioma
    if output_language == "pt":
        prompt += "\n\n**IMPORTANTE**: Toda a resposta deve ser em PORTUGUÊS BRASILEIRO."
    elif output_language == "en":
        prompt += "\n\n**IMPORTANT**: All responses must be in ENGLISH."
```

### 3. Arquivo de Progresso Estendido

**Novo formato `progress.json`:**
```json
{
    "source_type": "playlist",
    "source_id": "https://...",
    "language": ["pt", "en"],  ← Lista de idiomas preferidos
    "prompt_type": "copywriting",  ← Novo campo
    "output_language": "pt",  ← Novo campo
    "videos": [...],
    "current_index": 12,
    "total_videos": 61,
    "completed": false
}
```

### 4. Nomes de Arquivos Processados

**Padrão:**
```
{video_id}_{lang_legenda}_{prompt_type}_{output_lang}_processed.txt
```

**Exemplos:**
```
lB-wQFPMv9Y_pt_copywriting_pt_processed.txt
K-6CxJz51qo_en_faq_en_processed.txt
ABC123_kome_faq_pt_processed.txt
```

## 💡 Casos de Uso

### Caso 1: Playlist Multilíngue com FAQ em Português
```
Tipo de análise: FAQ
Idioma de saída: PT
Idiomas de legenda: pt,en,es

Resultado:
- Vídeos com legenda PT → transcrição PT → FAQ em PT
- Vídeos com legenda EN → transcrição EN → FAQ em PT
- Vídeos com legenda ES → transcrição ES → FAQ em PT
```

### Caso 2: Canal em Inglês com Copywriting em Inglês
```
Tipo de análise: Copywriting
Idioma de saída: EN
Idiomas de legenda: en

Resultado:
- Vídeos com legenda EN → transcrição EN → Copywriting em EN
- Vídeos sem legenda EN → pula ou usa outra disponível
```

### Caso 3: Aceitar Qualquer Legenda com FAQ em PT
```
Tipo de análise: FAQ
Idioma de saída: PT
Idiomas de legenda: (deixar vazio)

Resultado:
- Pega qualquer legenda disponível → FAQ sempre em PT
- Máxima cobertura de vídeos
```

## 🎯 Benefícios

### ✅ Flexibilidade
- Não precisa saber antecipadamente quais idiomas têm legenda
- Sistema adapta automaticamente

### ✅ Eficiência
- Prioriza idiomas preferidos
- Não desperdiça vídeos por falta de legenda específica

### ✅ Consistência
- Output sempre no idioma escolhido
- Independente do idioma da legenda

### ✅ Rastreabilidade
- Nome do arquivo identifica origem e processamento
- Fácil saber qual prompt foi usado

## 🔄 Compatibilidade com Retomada

O sistema de retomada continua funcionando:

```
⚠️  TAREFA INCOMPLETA DETECTADA!
Tipo: PLAYLIST
Idiomas preferidos: ['pt', 'en']
Tipo de análise: FAQ  ← Nova informação
Idioma de saída: PT   ← Nova informação
Progresso: 12/61 vídeos (19.7%)

[1] Continuar de onde parou
[2] Começar nova tarefa
```

## 📁 Estrutura de Arquivos

```
src/
├── prompt.txt                    # Prompt de copywriting
├── prompt_faq.txt               # Prompt de FAQ
├── transcriptions/              # Legendas baixadas
│   ├── video1_pt.txt
│   ├── video2_en.txt
│   └── video3_kome.txt
├── processed_transcriptions/    # Outputs da IA
│   ├── video1_pt_copywriting_pt_processed.txt
│   ├── video2_en_faq_en_processed.txt
│   └── video3_kome_faq_pt_processed.txt
└── output/
    ├── playlist_videos.json
    └── progress.json            # Com novos campos
```

## 🧪 Testando

### Teste 1: Múltiplos Idiomas
```bash
python3 app.py
# Escolha: FAQ, PT, pt,en,es
# Use uma playlist com vídeos em vários idiomas
# Verifique que todos são processados com FAQ em PT
```

### Teste 2: Retomada com Novo Sistema
```bash
# Inicie um processamento
python3 app.py
# Escolha: Copywriting, EN, en
# Interrompa com Ctrl+C após alguns vídeos

# Retome
python3 app.py
# Deve detectar e continuar com Copywriting, EN
```

### Teste 3: Qualquer Legenda
```bash
python3 app.py
# Tipo: FAQ, PT
# Idiomas: (deixe vazio)
# Deve aceitar qualquer legenda e gerar FAQ em PT
```

## ⚙️ Configurações Recomendadas

### Para Máxima Cobertura
```
Idiomas de legenda: (vazio)
```
Aceita qualquer legenda disponível.

### Para Conteúdo Brasileiro
```
Idiomas de legenda: pt,en
Tipo de análise: Copywriting
Idioma de saída: PT
```

### Para Conteúdo Internacional
```
Idiomas de legenda: en,pt,es
Tipo de análise: FAQ
Idioma de saída: EN
```

## 📝 Notas Importantes

1. **Idiomas de Legenda** ≠ **Idioma de Saída**
   - Legenda: O que está no vídeo do YouTube
   - Saída: Como a IA deve responder

2. **Prioridade Importa**
   - `pt,en` tenta PT primeiro
   - `en,pt` tenta EN primeiro

3. **Arquivos Não São Reprocessados**
   - Se já existe um arquivo com mesmo nome, pula
   - Para reprocessar, delete o arquivo anterior

4. **Progresso Salva Configurações**
   - Ao retomar, usa mesmas configurações
   - Não precisa reescolher tudo

## 🚀 Próximos Passos Sugeridos

1. **Auto-tradução**: Transcrever em um idioma e traduzir para outro antes da IA
2. **Prompts Customizados**: Permitir upload de prompts personalizados
3. **Batch Processing**: Processar múltiplas configurações de uma vez
4. **Preview**: Visualizar primeiros parágrafos antes de processar tudo
