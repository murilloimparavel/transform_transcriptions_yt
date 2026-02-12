import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import DeadlineExceeded

# Import from the sibling module
try:
    from .framework_processor import FrameworkProcessor, get_model
except ImportError:
    # Fallback for when running as script
    from framework_processor import FrameworkProcessor, get_model

class N8NFrameworkProcessor(FrameworkProcessor):
    """
    Processador especializado para análise de workflows n8n (JSON).
    """

    def __init__(self, json_content, output_language="pt"):
        """
        Args:
            json_content: String contendo o JSON do workflow (ou lista de workflows)
            output_language: Idioma de saída
        """
        super().__init__(json_content, output_language)
        
    def load_framework_prompt(self):
        """Carrega o prompt específico para n8n."""
        # Ajuste o caminho conforme necessário, assumindo estrutura atual
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_path, 'config', 'prompts', 'prompt_n8n_framework.txt')
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def create_dimension_prompt(self, dimension_number, dimension_name):
        """
        Cria um prompt focado em uma dimensão específica para n8n.
        """
        base_prompt = self.load_framework_prompt()
        dimension_marker = f"# **DIMENSÃO {dimension_number}:"
        next_dimension_marker = f"# **DIMENSÃO {dimension_number + 1}:"

        start = base_prompt.find(dimension_marker)
        if dimension_number < 7:
            end = base_prompt.find(next_dimension_marker)
        else:
            # Última dimensão vai até SÍNTESE FINAL
            end = base_prompt.find("# **SÍNTESE FINAL DO ESPECIALISTA**")

        if start == -1:
            raise ValueError(f"Dimensão {dimension_number} não encontrada no prompt")

        dimension_content = base_prompt[start:end if end != -1 else None]

        focused_prompt = f"""
Você é um Arquiteto de Automação Sênior especializado em n8n.

**TAREFA**: Extrair APENAS a **DIMENSÃO {dimension_number}: {dimension_name}** da documentação do workflow fornecida.

**INSTRUÇÕES**:
1. Analise o JSON do workflow COMPLETO.
2. Extraia TODOS os elementos solicitados nesta dimensão.
3. Seja EXTREMAMENTE TÉCNICO e ESPECÍFICO.
4. Cite nomes exatos de nós, parâmetros e expressões.
5. Se identificar más práticas, aponte-as.

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

{dimension_content}

---

**JSON DO(S) WORKFLOW(S) N8N PARA ANÁLISE**:

{self.transcription}

---

**AGORA EXTRAIA APENAS A DIMENSÃO {dimension_number} COM O MÁXIMO DE DETALHES TÉCNICOS**:
"""
        return focused_prompt

    def synthesize_framework(self):
        """
        Sintetiza todas as dimensões em uma documentação final.
        """
        print("\n🔗 Sintetizando documentação técnica...")

        dimensions_summary = "\n\n".join([
            f"## DIMENSÃO {num}: {data['name']}\n\n{data['content']}"
            for num, data in sorted(self.dimensions.items())
        ])

        synthesis_prompt = f"""
Você é um Arquiteto de Soluções Sênior.

**TAREFA**: Criar o VEREDITO TÉCNICO e SÍNTESE FINAL da análise do workflow n8n.

**INSTRUÇÕES**:
1. Dê uma nota técnica (0-10) baseada em boas práticas, segurança e performance.
2. Resuma os 3 pontos mais fortes e 3 pontos críticos de atenção.
3. Defina o "Próximo Passo Recomendado" (a ação mais prioritária).
4. Crie uma conclusão profissional sobre a maturidade da automação.

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

**ANÁLISE DETALHADA JÁ REALIZADA**:

{dimensions_summary}

---

**AGORA CRIE A SÍNTESE FINAL**:
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                current_model = get_model()
                chat = current_model.start_chat(history=[])
                response = chat.send_message(synthesis_prompt)

                self.synthesis = response.text.strip()
                print(f"✅ Síntese concluída ({len(self.synthesis)} caracteres)")
                return self.synthesis

            except DeadlineExceeded:
                if attempt < max_retries - 1:
                    print(f"⏳ Timeout - tentativa {attempt + 1}/{max_retries}")
                    time.sleep(5)
                else:
                    raise
            except Exception as e:
                # Se for erro de autenticação ou segurança, não adianta tentar de novo
                error_msg = str(e).lower()
                if "403" in error_msg or "api key" in error_msg:
                    print(f"🛑 Erro CRÍTICO de API: {e}")
                    raise RuntimeError(f"Erro crítico de API: {e}")

                if attempt < max_retries - 1:
                    print(f"⚠️  Erro - tentativa {attempt + 1}/{max_retries}: {e}")
                    time.sleep(5)
                else:
                    raise

    def save_complete_framework(self, output_path):
        """
        Salva a documentação técnica em arquivo.
        """
        final_document = f"""
# 🛠️ DOCUMENTAÇÃO TÉCNICA E OTIMIZAÇÃO - N8N

**Gerado em**: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
**Idioma**: {self.output_language.upper()}
**Input**: Análise de Workflow JSON

---

{self.synthesis}

---

"""
        # Adiciona todas as dimensões
        for num in sorted(self.dimensions.keys()):
            dim = self.dimensions[num]
            final_document += f"\n\n{'-' * 80}\n"
            final_document += f"\n# DIMENSÃO {num}: {dim['name'].upper()}\n\n"
            final_document += dim['content']
            final_document += f"\n\n{'-' * 80}\n"

        # Metadados
        final_document += f"""
---

## 📊 METADADOS DA ANÁLISE

- **Modelo utilizado**: {os.environ.get("LLM_MODEL", "gemini-2.5-flash")}
- **Timestamp**: {datetime.now().isoformat()}

**🤖 Gerado automaticamente pelo N8N Framework Processor**
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_document)

        print(f"💾 Documentação salva em: {output_path}")

        # Salva JSON estruturado
        json_path = output_path.replace('.txt', '.json')
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "language": self.output_language,
                "model": os.environ.get("LLM_MODEL", "gemini-2.5-flash"),
                "type": "n8n_analysis"
            },
            "synthesis": self.synthesis,
            "dimensions": self.dimensions
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    def process_complete_framework(self, output_path):
        print("=" * 80)
        print("🚀 INICIANDO ANÁLISE DE WORKFLOW N8N")
        print("=" * 80)

        dimensions_to_process = [
            (1, "VISÃO GERAL E ARQUITETURA"),
            (2, "ANÁLISE DE DADOS E TRANSFORMAÇÃO"),
            (3, "AUDITORIA DE NÓS E CONFIGURAÇÕES"),
            (4, "TRATAMENTO DE ERROS E RESILIÊNCIA"),
            (5, "PERFORMANCE E OTIMIZAÇÃO"),
            (6, "ESCALABILIDADE E MANUTENÇÃO"),
            (7, "PLANO DE MELHORIA E REFATORAÇÃO")
        ]

        for dim_num, dim_name in dimensions_to_process:
            try:
                self.process_dimension(dim_num, dim_name)
                if dim_num < 7:
                    print("⏳ Aguardando 10s...")
                    time.sleep(10)
            except RuntimeError as e:
                # Erro crítico (API Key, etc) - Aborta tudo
                print(f"🛑 Processamento ABORTADO na dimensão {dim_num}: {e}")
                print("⚠️  Verifique sua API KEY no arquivo .env")
                # Remove arquivo parcial se existir? Talvez não.
                print("❌ ANÁLISE FALHOU.")
                return
            except Exception as e:
                print(f"❌ Erro ao processar dimensão {dim_num}: {e}")
                continue

        try:
            self.synthesize_framework()
        except RuntimeError as e:
            print(f"🛑 Síntese ABORTADA: {e}")
            return
        except Exception as e:
            print(f"❌ Erro na síntese: {e}")
            self.synthesis = "Síntese não gerada devido a erro."

        self.save_complete_framework(output_path)
        
        print("\n" + "=" * 80)
        print("✅ ANÁLISE DE WORKFLOW CONCLUÍDA!")
        print("=" * 80)


def process_n8n_framework(json_input_path, output_language="pt"):
    """
    Função auxiliar para processar arquivo JSON do n8n.
    """
    # Lê JSON
    with open(json_input_path, 'r', encoding='utf-8') as f:
        json_content = f.read()

    # Valida se é JSON válido
    try:
        json_obj = json.loads(json_content)
        # Formata bonito para o prompt ler melhor
        formatted_json = json.dumps(json_obj, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        raise ValueError("O arquivo fornecido não é um JSON válido.")

    # Cria nome de saída
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'Framework_N8N')
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(json_input_path).replace('.json', '')
    output_path = os.path.join(output_dir, f"{base_name}_analysis_{output_language}.txt")

    if os.path.exists(output_path):
        print(f"⏭️  Análise já existe: {output_path}")
        return output_path

    processor = N8NFrameworkProcessor(formatted_json, output_language)
    processor.process_complete_framework(output_path)

    return output_path

