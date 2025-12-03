"""
Script para listar todos os modelos Gemini disponíveis.
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

print("🔍 Listando modelos disponíveis...\n")
print("=" * 80)

try:
    models = list(genai.list_models())
    
    # Filtra modelos que suportam generateContent
    available_models = [
        m for m in models 
        if 'generateContent' in m.supported_generation_methods
    ]
    
    print(f"\n✅ Total de modelos disponíveis: {len(available_models)}\n")
    
    # Agrupa por tipo
    flash_models = [m for m in available_models if 'flash' in m.name.lower()]
    pro_models = [m for m in available_models if 'pro' in m.name.lower() and 'flash' not in m.name.lower()]
    other_models = [m for m in available_models if 'flash' not in m.name.lower() and 'pro' not in m.name.lower()]
    
    if flash_models:
        print("📱 MODELOS FLASH (Rápidos):")
        for m in flash_models:
            name = m.name.replace('models/', '')
            print(f"   ✓ {name}")
        print()
    
    if pro_models:
        print("🚀 MODELOS PRO (Mais Poderosos):")
        for m in pro_models:
            name = m.name.replace('models/', '')
            print(f"   ✓ {name}")
        print()
    
    if other_models:
        print("📦 OUTROS MODELOS:")
        for m in other_models:
            name = m.name.replace('models/', '')
            print(f"   ✓ {name}")
        print()
    
    # Recomenda um modelo
    print("=" * 80)
    print("\n💡 RECOMENDAÇÃO:")
    
    if flash_models:
        recommended = flash_models[0].name.replace('models/', '')
        print(f"   Use: {recommended}")
        print(f"   (Modelo Flash mais recente disponível)")
    elif pro_models:
        recommended = pro_models[0].name.replace('models/', '')
        print(f"   Use: {recommended}")
        print(f"   (Modelo Pro disponível)")
    else:
        recommended = available_models[0].name.replace('models/', '')
        print(f"   Use: {recommended}")
        print(f"   (Primeiro modelo disponível)")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"❌ Erro ao listar modelos: {e}")
    import traceback
    traceback.print_exc()

