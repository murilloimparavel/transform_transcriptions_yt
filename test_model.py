"""
Script para testar se o modelo Gemini está configurado corretamente.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega variáveis do .env
load_dotenv()

# Configura API
api_key = os.getenv("API_KEY")
if not api_key:
    print("❌ ERRO: API_KEY não encontrada no .env")
    exit(1)

genai.configure(api_key=api_key)

# Obtém modelo do .env ou usa padrão
model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash-002").replace("models/", "")
print(f"🔍 Testando modelo: {model_name}")

try:
    # Tenta criar o modelo
    model = genai.GenerativeModel(model_name)
    print(f"✅ Modelo '{model_name}' criado com sucesso!")
    
    # Testa uma requisição simples
    print("\n🧪 Testando requisição...")
    response = model.generate_content("Diga 'OK' se você está funcionando.")
    print(f"✅ Resposta recebida: {response.text[:50]}...")
    
    print("\n✅ TUDO FUNCIONANDO! O modelo está configurado corretamente.")
    
except Exception as e:
    print(f"\n❌ ERRO ao usar o modelo '{model_name}':")
    print(f"   {e}")
    print("\n💡 Dica: Verifique se o modelo está correto no arquivo .env")
    print("   Modelos válidos: gemini-1.5-flash-002, gemini-1.5-pro")
    
    # Lista modelos disponíveis
    print("\n📋 Modelos Flash disponíveis:")
    try:
        models = list(genai.list_models())
        flash_models = [m.name for m in models if 'flash' in m.name.lower() and 'generateContent' in m.supported_generation_methods]
        for m in flash_models[:5]:
            print(f"   - {m}")
    except:
        print("   (Não foi possível listar modelos)")

