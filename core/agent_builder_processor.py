"""
Processador especializado para extração de conhecimento para agentes de IA.
Usa estratégia multi-stage para gerar bases de conhecimento otimizadas para RAG.
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import DeadlineExceeded

load_dotenv()

# Configura Gemini
genai.configure(api_key=os.environ["API_KEY"])

# Importa funções de modelo do framework_processor para reutilizar
from core.framework_processor import get_model


class AgentBuilderProcessor:
    """
    Processa transcrições para criar bases de conhecimento para agentes de IA.
    Extrai conhecimento em blocos estruturados otimizados para RAG.
    """

    def __init__(self, transcription_text, output_language="pt", source_name=""):
        self.transcription = transcription_text
        self.output_language = output_language
        self.source_name = source_name
        self.blocks = {}
        self.synthesis = None

    def load_agent_builder_prompt(self):
        """Carrega o prompt completo de agent builder."""
        prompt_path = os.path.join('config', 'prompts', 'agent_builder.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def create_block_prompt(self, block_number, block_name, block_description):
        """
        Cria um prompt focado em um bloco específico da extração.

        Args:
            block_number: Número do bloco (1-7)
            block_name: Nome do bloco
            block_description: Descrição do que extrair
        """
        base_prompt = self.load_agent_builder_prompt()

        # Extrai a seção relevante do prompt
        block_marker = f"## BLOCO {block_number}:"
        next_block_marker = f"## BLOCO {block_number + 1}:"

        start = base_prompt.find(block_marker)
        if block_number < 7:
            end = base_prompt.find(next_block_marker)
        else:
            end = base_prompt.find("# INSTRUÇÕES DE FORMATAÇÃO")

        if start == -1:
            # Se não encontrar o bloco específico, usa descrição manual
            block_content = block_description
        else:
            block_content = base_prompt[start:end if end != -1 else None]

        focused_prompt = f"""
Você é um Arquiteto de Conhecimento especializado em criar bases de dados para agentes de IA.

**TAREFA**: Extrair o **BLOCO {block_number}: {block_name}** do conteúdo fornecido.

**OBJETIVO**: Gerar conhecimento estruturado para que um Agente de IA possa responder perguntas sobre este assunto com precisão e profundidade.

**REGRAS CRÍTICAS**:
1. PRESERVE INFORMAÇÃO COMPLETA - Não resuma excessivamente
2. NUNCA INVENTE - Se não está no conteúdo, marque como [NÃO MENCIONADO]
3. MANTENHA LITERALIDADE - Citações, números e termos técnicos devem ser exatos
4. CHUNKS SEMÂNTICOS - Cada item deve fazer sentido isoladamente
5. METADADOS RICOS - Inclua tags e categorias para facilitar busca

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

{block_content}

---

**CONTEÚDO PARA ANÁLISE**:

{self.transcription}

---

**AGORA EXTRAIA O BLOCO {block_number} ({block_name}) SEGUINDO A ESTRUTURA YAML-LIKE**:
"""
        return focused_prompt

    def process_block(self, block_number, block_name, block_description):
        """
        Processa um bloco específico da extração.
        """
        print(f"\n🔍 Processando Bloco {block_number}: {block_name}")

        prompt = self.create_block_prompt(block_number, block_name, block_description)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                current_model = get_model()
                chat = current_model.start_chat(history=[])
                response = chat.send_message(prompt)

                result = response.text.strip()
                self.blocks[block_number] = {
                    "name": block_name,
                    "content": result,
                    "timestamp": datetime.now().isoformat()
                }

                print(f"✅ Bloco {block_number} concluído ({len(result)} caracteres)")
                return result

            except DeadlineExceeded:
                if attempt < max_retries - 1:
                    print(f"⏳ Timeout - tentativa {attempt + 1}/{max_retries}")
                    time.sleep(5)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Erro - tentativa {attempt + 1}/{max_retries}: {e}")
                    time.sleep(5)
                else:
                    raise

    def synthesize_knowledge_base(self):
        """
        Sintetiza todos os blocos em instruções finais para o agente.
        """
        print("\n🔗 Gerando instruções finais para o agente...")

        blocks_summary = "\n\n".join([
            f"## BLOCO {num}: {data['name']}\n\n{data['content']}"
            for num, data in sorted(self.blocks.items())
        ])

        synthesis_prompt = f"""
Você é um Arquiteto de Agentes de IA. Sua tarefa é criar as INSTRUÇÕES FINAIS para um agente especialista.

**TAREFA**: Com base em todos os blocos de conhecimento extraídos, crie:

1. **SYSTEM PROMPT SUGERIDO** (200-400 palavras)
   - Tom de comunicação do agente
   - Área de expertise
   - Limitações e o que o agente NÃO sabe
   - Frases características para usar

2. **REGRAS DE RESPOSTA** (10-15 regras)
   - Quando citar exemplos
   - Como lidar com perguntas fora do escopo
   - Prioridades de resposta
   - Conexões entre conceitos

3. **ÍNDICE DE CONHECIMENTO**
   - Lista categorizada de todos os tópicos cobertos
   - Mapa de conceitos relacionados
   - Lacunas identificadas

4. **EXEMPLOS DE INTERAÇÃO** (5-10 exemplos)
   - Pergunta típica
   - Resposta ideal do agente
   - Por que essa resposta é boa

5. **CHECKLIST DE VALIDAÇÃO**
   - Como verificar se o agente está respondendo corretamente
   - Red flags de respostas incorretas

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

**BLOCOS DE CONHECIMENTO EXTRAÍDOS**:

{blocks_summary}

---

**AGORA CRIE AS INSTRUÇÕES FINAIS PARA O AGENTE**:
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                current_model = get_model()
                chat = current_model.start_chat(history=[])
                response = chat.send_message(synthesis_prompt)

                self.synthesis = response.text.strip()
                print(f"✅ Instruções do agente concluídas ({len(self.synthesis)} caracteres)")
                return self.synthesis

            except DeadlineExceeded:
                if attempt < max_retries - 1:
                    print(f"⏳ Timeout - tentativa {attempt + 1}/{max_retries}")
                    time.sleep(5)
                else:
                    raise

    def save_knowledge_base(self, output_path):
        """
        Salva a base de conhecimento completa em arquivos estruturados.
        """
        # Documento principal (TXT para leitura humana)
        final_document = f"""
# 🤖 BASE DE CONHECIMENTO PARA AGENTE ESPECIALISTA

**Fonte**: {self.source_name or "Conteúdo processado"}
**Gerado em**: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
**Idioma**: {self.output_language.upper()}
**Tamanho do conteúdo original**: {len(self.transcription)} caracteres

---

# INSTRUÇÕES PARA O AGENTE

{self.synthesis or "[Síntese não gerada]"}

---

"""
        # Adiciona todos os blocos
        for num in sorted(self.blocks.keys()):
            block = self.blocks[num]
            final_document += f"\n{'=' * 80}\n"
            final_document += f"\n# BLOCO {num}: {block['name'].upper()}\n\n"
            final_document += block['content']
            final_document += f"\n\n{'=' * 80}\n"

        # Metadados finais
        final_document += f"""

---

## 📊 METADADOS DO PROCESSAMENTO

- **Total de blocos processados**: {len(self.blocks)}
- **Blocos disponíveis**: {', '.join([f"{k}: {v['name']}" for k, v in sorted(self.blocks.items())])}
- **Timestamp**: {datetime.now().isoformat()}
- **Modelo utilizado**: {os.environ.get("LLM_MODEL", "gemini-1.5-flash-002")}

---

**🤖 Gerado pelo YouTube Transcription Processor - Modo Agent Builder**
"""

        # Salva TXT
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_document)

        print(f"💾 Base de conhecimento salva em: {output_path}")

        # Salva JSON estruturado (para integração com sistemas RAG)
        json_path = output_path.replace('.txt', '.json')
        json_data = {
            "metadata": {
                "source": self.source_name,
                "generated_at": datetime.now().isoformat(),
                "language": self.output_language,
                "model": os.environ.get("LLM_MODEL", "gemini-1.5-flash-002"),
                "content_size": len(self.transcription),
                "type": "agent_knowledge_base"
            },
            "agent_instructions": self.synthesis,
            "knowledge_blocks": {
                str(k): {
                    "name": v["name"],
                    "content": v["content"],
                    "extracted_at": v["timestamp"]
                }
                for k, v in self.blocks.items()
            }
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"💾 JSON estruturado salvo em: {json_path}")

        return output_path

    def process_complete_knowledge_base(self, output_path):
        """
        Executa o processamento completo em todas as etapas.
        """
        print("=" * 80)
        print("🚀 INICIANDO EXTRAÇÃO PARA AGENT BUILDER")
        print("=" * 80)
        print(f"📄 Fonte: {self.source_name or 'Conteúdo'}")
        print(f"🌍 Idioma: {self.output_language.upper()}")
        print(f"📏 Tamanho: {len(self.transcription)} caracteres")
        print("=" * 80)

        # Define os 7 blocos de extração
        blocks_to_process = [
            (1, "ONTOLOGIA DO DOMÍNIO", "Glossário de termos, hierarquia de conceitos e relações"),
            (2, "BASE DE CONHECIMENTO FACTUAL", "Fatos, afirmações, números, métricas e fórmulas"),
            (3, "PROCEDIMENTOS E INSTRUÇÕES", "Processos passo a passo, árvores de decisão e checklists"),
            (4, "EXEMPLOS E CASOS", "Casos de estudo, histórias e comparações"),
            (5, "PERGUNTAS E RESPOSTAS", "Q&A extraídos e objeções com respostas"),
            (6, "CONTEXTO E METADADOS", "Informações da fonte, resumo e mapa de tópicos"),
            (7, "INSTRUÇÕES PARA O AGENTE", "Persona, regras de engajamento e conexões")
        ]

        # Processa cada bloco
        for block_num, block_name, block_desc in blocks_to_process:
            try:
                self.process_block(block_num, block_name, block_desc)
                # Rate limiting
                if block_num < 7:
                    print("⏳ Aguardando 20s antes do próximo bloco...")
                    time.sleep(20)
            except Exception as e:
                print(f"❌ Erro ao processar bloco {block_num}: {e}")
                continue

        # Sintetiza instruções do agente
        try:
            self.synthesize_knowledge_base()
        except Exception as e:
            print(f"❌ Erro na síntese: {e}")
            self.synthesis = "[Síntese não gerada devido a erro]"

        # Salva resultado
        self.save_knowledge_base(output_path)

        print("\n" + "=" * 80)
        print("✅ BASE DE CONHECIMENTO PARA AGENTE CRIADA COM SUCESSO!")
        print("=" * 80)

        return output_path


def process_transcription_agent_builder(input_file, output_language="pt"):
    """
    Função auxiliar para processar uma transcrição no modo Agent Builder.

    Args:
        input_file: Caminho do arquivo de transcrição
        output_language: Idioma de saída ('pt' ou 'en')

    Returns:
        str: Caminho do arquivo de saída
    """
    # Lê transcrição
    with open(input_file, 'r', encoding='utf-8') as f:
        transcription = f.read()

    # Cria nome de saída
    output_dir = os.path.join('data', 'processed')
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_file).replace('.txt', '')
    output_path = os.path.join(output_dir, f"{base_name}_agent_builder_{output_language}.txt")

    # Verifica se já foi processado
    if os.path.exists(output_path):
        print(f"⏭️  Base de conhecimento já existe: {output_path}")
        return output_path

    # Processa
    processor = AgentBuilderProcessor(transcription, output_language, base_name)
    processor.process_complete_knowledge_base(output_path)

    return output_path
