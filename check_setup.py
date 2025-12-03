"""
Script rápido para verificar se o projeto está configurado corretamente.
"""
import os
import sys
from pathlib import Path

def check():
    """Verifica configurações básicas."""
    print("\n" + "="*60)
    print("  VERIFICAÇÃO DE CONFIGURAÇÃO")
    print("="*60 + "\n")
    
    errors = []
    warnings = []
    
    # 1. Verificar Python
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    else:
        errors.append(f"Python {version.major}.{version.minor} - Requer 3.8+")
        print(f"✗ Python {version.major}.{version.minor} - Requer 3.8+")
    
    # 2. Verificar dependências
    print("\nVerificando dependências...")
    deps = {
        "google-generativeai": "google.generativeai",
        "python-dotenv": "dotenv",
        "pytube": "pytube",
        "youtube-transcript-api": "youtube_transcript_api",
        "requests": "requests",
        "termcolor": "termcolor"
    }
    
    for pkg_name, import_name in deps.items():
        try:
            __import__(import_name)
            print(f"  ✓ {pkg_name}")
        except ImportError:
            errors.append(f"Dependência faltando: {pkg_name}")
            print(f"  ✗ {pkg_name} - NÃO INSTALADO")
    
    # 3. Verificar arquivo .env
    print("\nVerificando configurações...")
    env_path = Path(".env")
    if env_path.exists():
        print("  ✓ Arquivo .env existe")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("API_KEY")
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        
        if not api_key or api_key == "sua_chave_gemini_aqui":
            warnings.append("API_KEY não configurada")
            print("  ⚠ API_KEY não configurada ou usando valor padrão")
        else:
            print("  ✓ API_KEY configurada")
        
        if not youtube_key or youtube_key == "sua_chave_youtube_aqui":
            warnings.append("YOUTUBE_API_KEY não configurada")
            print("  ⚠ YOUTUBE_API_KEY não configurada ou usando valor padrão")
        else:
            print("  ✓ YOUTUBE_API_KEY configurada")
    else:
        errors.append("Arquivo .env não encontrado")
        print("  ✗ Arquivo .env não encontrado")
        print("     Execute: copy env.example .env (Windows) ou cp env.example .env (Linux/Mac)")
    
    # 4. Verificar diretórios
    print("\nVerificando estrutura de diretórios...")
    dirs = [
        "data/transcriptions",
        "data/processed",
        "data/playlists",
        "data/progress",
        "logs",
        "config/prompts"
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ⚠ {dir_path} - Será criado automaticamente")
            path.mkdir(parents=True, exist_ok=True)
    
    # Resumo
    print("\n" + "="*60)
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        for error in errors:
            print(f"  - {error}")
        print("\nCorrija os erros antes de executar o projeto.")
        return False
    elif warnings:
        print("⚠️  AVISOS:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nO projeto pode não funcionar completamente sem essas configurações.")
        return True
    else:
        print("✅ TUDO CONFIGURADO CORRETAMENTE!")
        print("\nVocê pode executar: python app.py")
        return True
    print("="*60 + "\n")

if __name__ == "__main__":
    success = check()
    sys.exit(0 if success else 1)

