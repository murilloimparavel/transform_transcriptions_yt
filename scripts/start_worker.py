"""
Script para iniciar worker Celery.
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import celery_app

if __name__ == "__main__":
    print("🚀 Iniciando Celery Worker...")
    print("💡 Certifique-se de que o Redis está rodando")
    print("📝 Para iniciar Redis: redis-server (ou docker run -p 6379:6379 redis)")
    print("")
    
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4'
    ])

