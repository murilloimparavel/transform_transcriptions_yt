"""
Script de setup para verificar e configurar o ambiente do projeto.
"""
import os
import sys
import subprocess
from pathlib import Path

def print_status(message, status="INFO"):
    """Imprime mensagem formatada."""
    colors = {
        "INFO": "\033[94m",  # Azul
        "SUCCESS": "\033[92m",  # Verde
        "WARNING": "\033[93m",  # Amarelo
        "ERROR": "\033[91m",  # Vermelho
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}[{status}]{colors['RESET']} {message}")

def check_python_version():
    """Verifica a versão do Python."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Requer Python 3.8+", "ERROR")
        return False

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print_status("Verificando dependências...", "INFO")
    
    required_packages = [
        "google-generativeai",
        "python-dotenv",
        "pytube",
        "youtube-transcript-api",
        "requests",
        "termcolor"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_status(f"  ✓ {package}", "SUCCESS")
        except ImportError:
            print_status(f"  ✗ {package} - NÃO INSTALADO", "WARNING")
            missing.append(package)
    
    return missing

def install_dependencies():
    """Instala as dependências do requirements.txt."""
    print_status("Instalando dependências...", "INFO")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_status("Dependências instaladas com sucesso!", "SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Erro ao instalar dependências: {e}", "ERROR")
        return False

def check_env_file():
    """Verifica se o arquivo .env existe."""
    env_path = Path(".env")
    example_path = Path("env.example")
    
    if env_path.exists():
        print_status("Arquivo .env encontrado", "SUCCESS")
        
        # Verifica se as variáveis obrigatórias estão configuradas
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("API_KEY")
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        
        if not api_key or api_key == "sua_chave_gemini_aqui":
            print_status("  ⚠ API_KEY não configurada ou usando valor padrão", "WARNING")
        else:
            print_status("  ✓ API_KEY configurada", "SUCCESS")
        
        if not youtube_key or youtube_key == "sua_chave_youtube_aqui":
            print_status("  ⚠ YOUTUBE_API_KEY não configurada ou usando valor padrão", "WARNING")
        else:
            print_status("  ✓ YOUTUBE_API_KEY configurada", "SUCCESS")
        
        return True
    else:
        print_status("Arquivo .env não encontrado", "WARNING")
        if example_path.exists():
            print_status("Copiando env.example para .env...", "INFO")
            import shutil
            shutil.copy(example_path, env_path)
            print_status("Arquivo .env criado! Configure suas chaves API.", "SUCCESS")
        else:
            print_status("Arquivo env.example não encontrado. Crie um arquivo .env manualmente.", "ERROR")
        return False

def check_directories():
    """Verifica se os diretórios necessários existem."""
    print_status("Verificando estrutura de diretórios...", "INFO")
    
    required_dirs = [
        "data/transcriptions",
        "data/processed",
        "data/playlists",
        "data/progress",
        "data/proxies",
        "logs",
        "config/prompts"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print_status(f"  ✓ {dir_path}", "SUCCESS")
        else:
            print_status(f"  ✗ {dir_path} - Criando...", "WARNING")
            path.mkdir(parents=True, exist_ok=True)
            print_status(f"  ✓ {dir_path} criado", "SUCCESS")

def main():
    """Função principal do setup."""
    print("\n" + "="*60)
    print("  SETUP - YouTube Transcription Processor")
    print("="*60 + "\n")
    
    # Verifica versão do Python
    if not check_python_version():
        print_status("Por favor, instale Python 3.8 ou superior.", "ERROR")
        sys.exit(1)
    
    # Verifica dependências
    missing = check_dependencies()
    
    if missing:
        print_status(f"\n{len(missing)} dependência(s) faltando.", "WARNING")
        install = input("Deseja instalar as dependências agora? (s/n): ").strip().lower()
        if install == 's':
            if not install_dependencies():
                print_status("Falha ao instalar dependências. Instale manualmente com: pip install -r requirements.txt", "ERROR")
                sys.exit(1)
        else:
            print_status("Instale as dependências manualmente com: pip install -r requirements.txt", "WARNING")
    
    # Verifica estrutura de diretórios
    check_directories()
    
    # Verifica arquivo .env
    check_env_file()
    
    print("\n" + "="*60)
    print_status("Setup concluído!", "SUCCESS")
    print("="*60)
    print("\nPróximos passos:")
    print("1. Configure suas chaves API no arquivo .env")
    print("2. Execute: python app.py")
    print("\n")

if __name__ == "__main__":
    main()

