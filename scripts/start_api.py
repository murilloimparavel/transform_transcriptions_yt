"""
Script para iniciar a API.
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from config.settings import settings

if __name__ == "__main__":
    print(f"🚀 Iniciando API em http://{settings.api_host}:{settings.api_port}")
    print(f"📚 Documentação: http://{settings.api_host}:{settings.api_port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

