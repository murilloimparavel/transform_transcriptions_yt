"""
Script para iniciar o frontend Streamlit.
"""
import sys
import os
import subprocess

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

if __name__ == "__main__":
    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend",
        "app.py"
    )
    
    print(f"🚀 Iniciando Frontend em http://localhost:{settings.frontend_port}")
    
    subprocess.run([
        "streamlit", "run", frontend_path,
        "--server.port", str(settings.frontend_port)
    ])

