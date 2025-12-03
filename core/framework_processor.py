"""
Processador especializado para extração de frameworks completos.
Usa estratégia multi-stage para lidar com limitações de contexto.
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

# Cache do modelo válido para evitar múltiplas tentativas
_valid_model_cache = None

def get_available_models():
    """
    Lista modelos disponíveis que suportam generateContent.
    """
    try:
        models = list(genai.list_models())
        available = [
            m.name.replace('models/', '') 
            for m in models 
            if 'generateContent' in m.supported_generation_methods
        ]
        return available
    except Exception as e:
        print(f"⚠️  Erro ao listar modelos: {e}")
        return []

def find_valid_model(preferred_name=None):
    """
    Encontra um modelo válido, tentando o preferido primeiro.
    """
    global _valid_model_cache
    
    # Se já temos um modelo válido em cache, usa ele
    if _valid_model_cache:
        return _valid_model_cache
    
    # Lista modelos disponíveis
    available = get_available_models()
    
    if not available:
        # Fallback para modelos comuns se não conseguir listar
        fallback_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash",
            "gemini-1.5-pro-latest",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        
        for model_name in fallback_models:
            try:
                model = genai.GenerativeModel(model_name)
                _valid_model_cache = model_name
                print(f"✅ Modelo válido encontrado (fallback): {model_name}")
                return model_name
            except:
                continue
        
        raise ValueError("Nenhum modelo Gemini disponível encontrado!")
    
    # Se tem modelo preferido, tenta primeiro
    if preferred_name:
        preferred_clean = preferred_name.replace('models/', '').strip()
        if preferred_clean in available:
            _valid_model_cache = preferred_clean
            print(f"✅ Usando modelo preferido: {preferred_clean}")
            return preferred_clean
    
    # Procura por modelos flash primeiro
    flash_models = [m for m in available if 'flash' in m.lower()]
    if flash_models:
        model_name = flash_models[0]
        _valid_model_cache = model_name
        print(f"✅ Usando modelo Flash disponível: {model_name}")
        return model_name
    
    # Se não tem flash, usa o primeiro disponível
    model_name = available[0]
    _valid_model_cache = model_name
    print(f"✅ Usando primeiro modelo disponível: {model_name}")
    return model_name

def get_model():
    """
    Obtém o modelo Gemini configurado.
    Cria o modelo dinamicamente para garantir que sempre use o valor atual do .env
    """
    # Recarrega .env para garantir valor atualizado
    load_dotenv(override=True)
    
    # Obtém modelo preferido do .env
    preferred_model = os.environ.get("LLM_MODEL", "").replace("models/", "").strip()
    
    # Garante que não está usando modelo antigo conhecido como inválido
    if preferred_model in ["gemini-1.5-flash", "gemini-2.5-flash"]:
        print(f"⚠️  Modelo '{preferred_model}' não é válido. Procurando alternativas...")
        preferred_model = None
    
    # Encontra modelo válido
    try:
        model_name = find_valid_model(preferred_model)
        print(f"🤖 Usando modelo: {model_name}")
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"❌ Erro ao encontrar modelo válido: {e}")
        # Última tentativa com modelo padrão da biblioteca
        print("🔄 Tentando modelo padrão da biblioteca...")
        return genai.GenerativeModel()  # Usa padrão da biblioteca


class FrameworkProcessor:
    """
    Processa transcrições grandes extraindo frameworks em múltiplas etapas.
    """

    def __init__(self, transcription_text, output_language="pt"):
        self.transcription = transcription_text
        self.output_language = output_language
        self.dimensions = {}
        self.synthesis = None

    def load_framework_prompt(self):
        """Carrega o prompt completo de framework."""
        prompt_path = os.path.join('config', 'prompts', 'prompt_framework.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def create_dimension_prompt(self, dimension_number, dimension_name):
        """
        Cria um prompt focado em uma dimensão específica.

        Args:
            dimension_number: Número da dimensão (1-7)
            dimension_name: Nome descritivo da dimensão
        """
        base_prompt = self.load_framework_prompt()

        # Extrai apenas a seção relevante do prompt
        dimension_marker = f"# **DIMENSÃO {dimension_number}:"
        next_dimension_marker = f"# **DIMENSÃO {dimension_number + 1}:"

        # Encontra início e fim da dimensão
        start = base_prompt.find(dimension_marker)
        if dimension_number < 7:
            end = base_prompt.find(next_dimension_marker)
        else:
            # Última dimensão vai até RECURSOS COMPLEMENTARES
            end = base_prompt.find("# **RECURSOS COMPLEMENTARES**")

        if start == -1:
            raise ValueError(f"Dimensão {dimension_number} não encontrada no prompt")

        dimension_content = base_prompt[start:end if end != -1 else None]

        # Cria prompt focado
        focused_prompt = f"""
Você é um especialista em extrair frameworks de implementação de conteúdos educacionais.

**TAREFA**: Extrair APENAS a **DIMENSÃO {dimension_number}: {dimension_name}** da transcrição fornecida.

**INSTRUÇÕES**:
1. Leia a transcrição COMPLETA antes de responder
2. Extraia TODOS os elementos solicitados nesta dimensão
3. Seja EXTREMAMENTE detalhado e específico
4. Use exemplos EXATOS da transcrição (com números, nomes, casos)
5. NÃO invente informações - apenas extraia o que está no texto
6. Se algo não estiver mencionado, escreva "Não mencionado na transcrição"

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

{dimension_content}

---

**TRANSCRIÇÃO COMPLETA PARA ANÁLISE**:

{self.transcription}

---

**AGORA EXTRAIA APENAS A DIMENSÃO {dimension_number} COM O MÁXIMO DE DETALHES POSSÍVEL**:
"""
        return focused_prompt

    def process_dimension(self, dimension_number, dimension_name):
        """
        Processa uma dimensão específica do framework.
        """
        print(f"\n🔍 Processando Dimensão {dimension_number}: {dimension_name}")

        prompt = self.create_dimension_prompt(dimension_number, dimension_name)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Cria modelo dinamicamente para garantir valor correto
                current_model = get_model()
                chat = current_model.start_chat(history=[])
                response = chat.send_message(prompt)

                result = response.text.strip()
                self.dimensions[dimension_number] = {
                    "name": dimension_name,
                    "content": result,
                    "timestamp": datetime.now().isoformat()
                }

                print(f"✅ Dimensão {dimension_number} concluída ({len(result)} caracteres)")
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

    def synthesize_framework(self):
        """
        Sintetiza todas as dimensões em um framework coeso final.
        """
        print("\n🔗 Sintetizando framework completo...")

        # Monta resumo de todas as dimensões
        dimensions_summary = "\n\n".join([
            f"## DIMENSÃO {num}: {data['name']}\n\n{data['content']}"
            for num, data in sorted(self.dimensions.items())
        ])

        synthesis_prompt = f"""
Você é um especialista em sintetizar frameworks de implementação.

**TAREFA**: Criar a síntese final do framework completo, integrando todas as 7 dimensões processadas.

**INSTRUÇÕES**:
1. Crie o SUMÁRIO EXECUTIVO TRANSFORMADOR (3 parágrafos densos)
2. Crie a SÍNTESE FINAL MEMORÁVEL
3. Crie o GUIA DE INÍCIO IMEDIATO
4. Identifique conexões entre dimensões
5. Destaque os 3 insights mais transformadores
6. Crie um plano de ação de 30-60-90 dias integrado

**IDIOMA DE SAÍDA**: {"Português Brasileiro" if self.output_language == "pt" else "English"}

---

**TODAS AS DIMENSÕES JÁ PROCESSADAS**:

{dimensions_summary}

---

**AGORA CRIE A SÍNTESE FINAL INTEGRADORA**:
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Cria modelo dinamicamente para garantir valor correto
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

    def save_complete_framework(self, output_path):
        """
        Salva o framework completo em um arquivo estruturado.
        """
        # Monta documento final
        final_document = f"""
# 📚 FRAMEWORK COMPLETO DE IMPLEMENTAÇÃO

**Gerado em**: {datetime.now().strftime("%d/%m/%Y às %H:%M")}
**Idioma**: {self.output_language.upper()}
**Tamanho da transcrição**: {len(self.transcription)} caracteres

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

        # Adiciona metadados ao final
        final_document += f"""

---

## 📊 METADADOS DO PROCESSAMENTO

- **Total de dimensões processadas**: {len(self.dimensions)}
- **Timestamp da síntese**: {self.synthesis and datetime.now().isoformat()}
- **Tamanho total do framework**: ~{len(final_document)} caracteres
- **Processado com**: {os.environ.get("LLM_MODEL", "gemini-1.5-flash-002")}

---

**🤖 Gerado automaticamente pelo YouTube Transcription Processor**
"""

        # Salva arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_document)

        print(f"💾 Framework completo salvo em: {output_path}")

        # Também salva JSON estruturado para processamento posterior
        json_path = output_path.replace('.txt', '.json')
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "language": self.output_language,
                "model": os.environ.get("LLM_MODEL", "gemini-1.5-flash-002"),
                "transcription_size": len(self.transcription)
            },
            "synthesis": self.synthesis,
            "dimensions": self.dimensions
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"💾 Metadados salvos em: {json_path}")

    def process_complete_framework(self, output_path):
        """
        Executa o processamento completo do framework em todas as etapas.
        """
        print("=" * 80)
        print("🚀 INICIANDO EXTRAÇÃO DE FRAMEWORK COMPLETO")
        print("=" * 80)

        # Define as 7 dimensões
        dimensions_to_process = [
            (1, "FRAMEWORK COMPLETO DE IMPLEMENTAÇÃO"),
            (2, "INSIGHTS REVOLUCIONÁRIOS"),
            (3, "ASPECTOS CONTRA-INTUITIVOS"),
            (4, "HISTÓRIAS E CASOS TRANSFORMADORES"),
            (5, "NÚMEROS E FÓRMULAS EXATAS"),
            (6, "APLICAÇÕES IMEDIATAS PÓS-LEITURA"),
            (7, "CITAÇÕES ESTRATÉGICAS E MANTRAS")
        ]

        # Processa cada dimensão
        for dim_num, dim_name in dimensions_to_process:
            try:
                self.process_dimension(dim_num, dim_name)
                # Rate limiting - espera entre dimensões
                if dim_num < 7:
                    print("⏳ Aguardando 20s antes da próxima dimensão...")
                    time.sleep(20)
            except Exception as e:
                print(f"❌ Erro ao processar dimensão {dim_num}: {e}")
                # Continua com as outras dimensões
                continue

        # Sintetiza tudo
        try:
            self.synthesize_framework()
        except Exception as e:
            print(f"❌ Erro na síntese: {e}")
            print("⚠️  Continuando sem síntese...")
            self.synthesis = "Síntese não gerada devido a erro."

        # Salva resultado final
        self.save_complete_framework(output_path)

        print("\n" + "=" * 80)
        print("✅ FRAMEWORK COMPLETO EXTRAÍDO COM SUCESSO!")
        print("=" * 80)


def process_transcription_framework(input_file, output_language="pt"):
    """
    Função auxiliar para processar uma transcrição com extração de framework.

    Args:
        input_file: Caminho do arquivo de transcrição
        output_language: Idioma de saída ('pt' ou 'en')
    """
    # Lê transcrição
    with open(input_file, 'r', encoding='utf-8') as f:
        transcription = f.read()

    # Cria nome de saída
    output_dir = os.path.join('data', 'processed')
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(input_file).replace('.txt', '')
    output_path = os.path.join(output_dir, f"{base_name}_framework_{output_language}.txt")

    # Verifica se já foi processado
    if os.path.exists(output_path):
        print(f"⏭️  Framework já existe: {output_path}")
        return output_path

    # Processa
    processor = FrameworkProcessor(transcription, output_language)
    processor.process_complete_framework(output_path)

    return output_path
