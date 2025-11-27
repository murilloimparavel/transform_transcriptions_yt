import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import DeadlineExceeded

# Carrega as variáveis do .env
load_dotenv()

# Configura a API do Gemini usando a chave da API do .env
genai.configure(api_key=os.environ["API_KEY"])

# Inicializa o modelo Gemini usando a configuração do .env
model_name = os.environ.get("LLM_MODEL", "gemini-1.5-flash")
model = genai.GenerativeModel(model_name)

def split_text_into_chunks(transcription_text, max_chunk_size=10000):
    return [transcription_text[i:i+max_chunk_size] for i in range(0, len(transcription_text), max_chunk_size)]

def load_prompt(prompt_type="copywriting", output_language="pt"):
    """
    Carrega o prompt apropriado baseado no tipo selecionado.

    Args:
        prompt_type: 'faq' ou 'copywriting'
        output_language: 'pt' ou 'en'

    Returns:
        str: Conteúdo do prompt com instruções de idioma
    """
    if prompt_type == "faq":
        prompt_path = os.path.join('config', 'prompts', 'faq.txt')
    else:
        prompt_path = os.path.join('config', 'prompts', 'copywriting.txt')

    with open(prompt_path, 'r', encoding='utf-8') as file:
        prompt_content = file.read()

    # Adiciona instrução de idioma ao prompt
    language_instruction = {
        "pt": "\n\n**IMPORTANTE**: Toda a resposta deve ser em PORTUGUÊS BRASILEIRO.",
        "en": "\n\n**IMPORTANT**: All responses must be in ENGLISH."
    }

    return prompt_content + language_instruction.get(output_language, "")

def interview_transcription_with_gemini(chunk, prompt):
    chat = model.start_chat(
        history=[
            {"role": "user", "parts": prompt + "\n\n" + chunk}
        ]
    )
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = chat.send_message(prompt + "\n\n" + chunk)
            return response.text.strip()
        except DeadlineExceeded:
            if attempt < max_retries - 1:
                print(f"Timeout ao processar chunk. Tentativa {attempt + 1} de {max_retries}...")
                time.sleep(2)
            else:
                raise

def process_transcription(input_file, prompt_type="copywriting", output_language="pt"):
    """
    Processa uma transcrição já salva em `src/transcriptions`
    e gera a saída em `src/processed_transcriptions`.

    Args:
        input_file: Caminho do arquivo de transcrição
        prompt_type: 'faq' ou 'copywriting'
        output_language: 'pt' ou 'en'
    """
    output_dir = os.path.join('data', 'processed')
    os.makedirs(output_dir, exist_ok=True)

    # Nome base preservando "_kome" ou "_pt" e adicionando tipo de prompt
    base_name = os.path.basename(input_file).replace(".txt", f"_{prompt_type}_{output_language}_processed.txt")
    output_file = os.path.join(output_dir, base_name)

    # Verifica se já foi processado
    if os.path.exists(output_file):
        print(f"⏭️  Arquivo já processado: {output_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as file:
        transcription_text = file.read()

    chunks = split_text_into_chunks(transcription_text)
    prompt = load_prompt(prompt_type, output_language)

    for index, chunk in enumerate(chunks):
        print(f"Processando chunk {index + 1}/{len(chunks)} de tamanho {len(chunk)} para {input_file}")

        processed_chunk = interview_transcription_with_gemini(chunk, prompt)

        with open(output_file, 'a', encoding='utf-8') as out_file:
            out_file.write(processed_chunk + "\n\n")

        if (index + 1) % 15 == 0:
            print("Atingido o limite de 15 requisições por minuto. Aguardando 60 segundos...")
            time.sleep(60)

    print(f"✅ Transcrição processada salva em {output_file}")

if __name__ == "__main__":
    file_name = input("Digite o nome do arquivo (com extensão) em 'src/transcriptions': ").strip()
    file_path = os.path.join("src", "transcriptions", file_name)
    process_transcription(file_path)
