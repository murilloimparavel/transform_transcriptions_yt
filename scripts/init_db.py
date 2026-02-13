"""
Script para inicializar o banco de dados.
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database.database import init_db, engine
from api.database import models

def main():
    """Inicializa o banco de dados."""
    print("🔧 Inicializando banco de dados...")
    
    # Cria todas as tabelas
    models.Base.metadata.create_all(bind=engine)
    
    print("✅ Banco de dados inicializado com sucesso!")
    print(f"📁 Localização: {engine.url}")

if __name__ == "__main__":
    main()

