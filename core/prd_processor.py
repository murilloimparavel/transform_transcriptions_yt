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

class PRDProcessor(FrameworkProcessor):
    """
    Processador especializado para criação de PRDs (Product Requirements Documents)
    baseados na metodologia BMAD.
    """

    def __init__(self, content, output_language="pt"):
        """
        Args:
            content: Texto contendo o conteúdo base (transcrição, docs, etc)
            output_language: Idioma de saída
        """
        super().__init__(content, output_language)
        
    def load_framework_prompt(self):
        """Carrega o prompt específico para PRD BMAD."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_path, 'config', 'prompts', 'prompt_prd_bmad.txt')
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def create_dimension_prompt(self, dimension_number, dimension_name):
        """
        Cria um prompt focado em uma dimensão específica do PRD.
        """
        base_prompt = self.load_framework_prompt()
        dimension_marker = f"# **DIMENSÃO {dimension_number}:"
        next_dimension_marker = f"# **DIMENSÃO {dimension_number + 1}:"

        start = base_prompt.find(dimension_marker)
        if dimension_number < 7:
            end = base_prompt.find(next_dimension_marker)
        else:
            # Última dimensão vai até SÍNTESE DO ARQUITETO
            end = base_prompt.find("# **SÍNTESE DO ARQUITETO (Conclusão)**")

        if start == -1:
            raise ValueError(f"Dimensão {dimension_number} não encontrada no prompt")

        dimension_content = base_prompt[start:end if end != -1 else None]

        focused_prompt = f"""
Você é um Product Manager Sênior e Arquiteto de Soluções especialista em metodologia BMAD.

**TAREFA**: Criar APENAS a **DIMENSÃO {dimension_number}: {dimension_name}** do PRD.

**INSTRUÇÕES**:
1. Analise TODO o conteúdo fornecido como referência.
2. Extraia, defina e especifique os requisitos para esta dimensão.
3. Use a metodologia BMAD (Building Multi-Agent Development) para garantir qualidade e completude.
4. Seja técnico, direto e orientado a implementação.
5. Se faltar informação no input, faça suposições lógicas baseadas em melhores práticas de mercado e marque como [SUGESTÃO].

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

{dimension_content}

---

**CONTEÚDO DE REFERÊNCIA (TRANSCRIÇÃO/DOCS/SITES)**:

{self.transcription}

---

**AGORA ESCREVA APENAS A DIMENSÃO {dimension_number} DO PRD**:
"""
        return focused_prompt

    def synthesize_framework(self):
        """
        Sintetiza o PRD completo com uma conclusão executiva.
        """
        print("\n🔗 Sintetizando PRD completo...")

        dimensions_summary = "\n\n".join([
            f"## DIMENSÃO {num}: {data['name']}\n\n{data['content']}"
            for num, data in sorted(self.dimensions.items())
        ])

        synthesis_prompt = f"""
Você é um CTO / VP de Engenharia avaliando um PRD recém-criado.

**TAREFA**: Criar a SÍNTESE DO ARQUITETO e CONCLUSÃO EXECUTIVA para este PRD.

**INSTRUÇÕES**:
1. Avalie a viabilidade técnica geral do projeto.
2. Identifique os maiores desafios de engenharia.
3. Dê uma recomendação final clara para o time de desenvolvimento (Go / No-Go / Adjust).
4. Resuma o potencial de impacto do produto.

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

**PRD GERADO (DIMENSÕES 1-7)**:

{dimensions_summary}

---

**AGORA CRIE A SÍNTESE DO ARQUITETO**:
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

            except Exception as e:
                # Tratamento de erro similar ao do processador base
                error_msg = str(e).lower()
                if "403" in error_msg or "api key" in error_msg:
                    print(f"🛑 Erro CRÍTICO de API na síntese: {e}")
                    raise RuntimeError(f"Erro crítico de API: {e}")
                
                if attempt < max_retries - 1:
                    print(f"⏳ Erro na síntese - tentativa {attempt + 1}/{max_retries}: {e}")
                    time.sleep(5)
                else:
                    print(f"❌ Falha na síntese após tentativas: {e}")
                    self.synthesis = "Síntese não gerada devido a erro."
                    return self.synthesis

    def save_complete_framework(self, output_path):
        """
        Salva o PRD em arquivo.
        """
        final_document = f"""
# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD) - BMAD METHODOLOGY

**Gerado em**: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
**Idioma**: {self.output_language.upper()}
**Baseado em**: Análise de conteúdo fornecido

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

## 📊 METADADOS DO DOCUMENTO

- **Metodologia**: BMAD (Building Multi-Agent Development)
- **Modelo utilizado**: {os.environ.get("LLM_MODEL", "gemini-2.5-flash")}
- **Timestamp**: {datetime.now().isoformat()}

**🤖 Gerado automaticamente pelo PRD BMAD Processor**
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_document)

        print(f"💾 PRD salvo em: {output_path}")

        # Salva JSON
        json_path = output_path.replace('.txt', '.json')
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "language": self.output_language,
                "model": os.environ.get("LLM_MODEL", "gemini-2.5-flash"),
                "type": "prd_bmad"
            },
            "synthesis": self.synthesis,
            "dimensions": self.dimensions
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    def process_complete_framework(self, output_path):
        print("=" * 80)
        print("🚀 INICIANDO CRIAÇÃO DE PRD (BMAD)")
        print("=" * 80)

        dimensions_to_process = [
            (1, "ESCOPO E VISÃO DO PRODUTO"),
            (2, "REQUISITOS FUNCIONAIS"),
            (3, "ARQUITETURA TÉCNICA"),
            (4, "UX/UI E FRONTEND"),
            (5, "REQUISITOS NÃO-FUNCIONAIS E SEGURANÇA"),
            (6, "PLANO DE IMPLEMENTAÇÃO"),
            (7, "RISCOS E MITIGAÇÃO")
        ]

        for dim_num, dim_name in dimensions_to_process:
            try:
                self.process_dimension(dim_num, dim_name)
                if dim_num < 7:
                    print("⏳ Aguardando 10s...")
                    time.sleep(10)
            except RuntimeError as e:
                print(f"🛑 Processamento ABORTADO na dimensão {dim_num}: {e}")
                print("⚠️  Verifique sua API KEY no arquivo .env")
                print("❌ GERAÇÃO DE PRD FALHOU.")
                return
            except Exception as e:
                print(f"❌ Erro ao processar dimensão {dim_num}: {e}")
                continue

        try:
            self.synthesize_framework()
        except Exception as e:
             print(f"❌ Erro na síntese final: {e}")

        self.save_complete_framework(output_path)
        
        print("\n" + "=" * 80)
        print("✅ PRD GERADO COM SUCESSO!")
        print("=" * 80)


def process_prd_framework(input_path, output_language="pt"):
    """
    Função auxiliar para processar input e gerar PRD.
    Args:
        input_path: Caminho para arquivo de texto/transcrição/json
        output_language: 'pt' ou 'en'
    """
    # Lê conteúdo
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo {input_path}: {e}")
        raise

    # Cria nome de saída
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed', 'PRD_BMAD')
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_path).replace('.txt', '').replace('.json', '').replace('.md', '')
    output_path = os.path.join(output_dir, f"PRD_{base_name}_{output_language}.txt")

    if os.path.exists(output_path):
        print(f"⏭️  PRD já existe: {output_path}")
        return output_path

    processor = PRDProcessor(content, output_language)
    processor.process_complete_framework(output_path)

    return output_path

