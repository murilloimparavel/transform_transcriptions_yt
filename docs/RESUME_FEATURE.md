# 🔄 Funcionalidade de Retomada Automática

## O que foi implementado

O sistema agora detecta automaticamente quando uma execução foi interrompida e oferece a opção de continuar de onde parou.

## Como funciona

### 1. Detecção Automática
Quando você executa `app.py`, o sistema verifica automaticamente se existe alguma tarefa incompleta:

```
⚠️  TAREFA INCOMPLETA DETECTADA!
Tipo: PLAYLIST
Fonte: https://www.youtube.com/playlist?list=...
Idioma: pt
Progresso: 13/61 vídeos (21.3%)
Última atualização: 2025-11-26T10:00:00

[1] Continuar de onde parou
[2] Começar uma nova tarefa (apaga o progresso anterior)
```

### 2. Gerenciamento de Progresso
- Cada vídeo processado é registrado no arquivo `src/output/progress.json`
- O sistema verifica se a transcrição já existe antes de tentar baixar novamente
- Mesmo se você interromper com `Ctrl+C`, o progresso é salvo

### 3. Retomada Inteligente
- Pula automaticamente vídeos já transcritos
- Continua exatamente do próximo vídeo não processado
- Mantém configurações originais (idioma, fonte, etc)

## Arquivos Criados/Modificados

### Novos Arquivos
- `functions/progress_manager.py` - Gerenciador de progresso completo

### Arquivos Modificados
1. **app.py**:
   - Detecção automática de tarefas incompletas
   - Sistema de retomada integrado
   - Melhor tratamento de interrupções (Ctrl+C)

2. **functions/get_playlist.py**:
   - Correção do bug de URLs duplicadas

3. **functions/get_transcription.py**:
   - Atualização para nova API do youtube-transcript-api
   - Melhor compatibilidade e confiabilidade

## Arquivo de Progresso

O arquivo `src/output/progress.json` contém:

```json
{
    "source_type": "playlist",
    "source_id": "URL_ou_ID",
    "language": "pt",
    "videos": [...],
    "current_index": 13,
    "total_videos": 61,
    "completed": false,
    "last_update": "2025-11-26T10:00:00"
}
```

## Como Usar

### Executar Nova Tarefa
```bash
python3 app.py
```

Se não houver tarefa incompleta, o fluxo normal será executado.

### Retomar Tarefa Interrompida
```bash
python3 app.py
```

Se houver tarefa incompleta, você verá as opções:
- **Opção 1**: Continua de onde parou
- **Opção 2**: Apaga o progresso e começa nova tarefa

### Interromper com Segurança
- Pressione `Ctrl+C` a qualquer momento
- O progresso até o último vídeo processado será salvo
- Na próxima execução, você pode retomar

## Benefícios

✅ **Economia de tempo**: Não precisa reprocessar vídeos já baixados
✅ **Resiliência**: Interrupções não causam perda de progresso
✅ **Transparência**: Você sempre sabe onde está no processamento
✅ **Automático**: Detecção e retomada sem comandos extras
✅ **Inteligente**: Pula vídeos já processados automaticamente

## Exemplos de Uso

### Cenário 1: Playlist Grande
1. Você inicia o download de uma playlist com 100 vídeos
2. Após 30 vídeos, você precisa desligar o computador
3. Na próxima execução, o sistema detecta automaticamente
4. Você escolhe "Continuar de onde parou"
5. O sistema retoma do vídeo 31

### Cenário 2: Erro em um Vídeo
1. Um vídeo específico está causando erro
2. O sistema marca como processado e continua
3. Você pode revisar os logs depois
4. O processamento não trava

### Cenário 3: Verificação de Transcrições Existentes
1. Você já tem algumas transcrições na pasta `src/transcriptions`
2. O sistema detecta automaticamente
3. Pula esses vídeos sem tentar baixar novamente
4. Economiza tempo e requisições à API

## Limpeza Manual

Se quiser forçar uma nova execução:
```bash
rm src/output/progress.json
```

## Observações

- O progresso é salvo a cada vídeo processado
- Mesmo com erro, o vídeo é marcado como processado para evitar loops
- Os logs em `logs/transcriptions.log` contêm detalhes de cada operação
