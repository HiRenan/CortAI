import os # Importa o módulo os
import sys # Importa o módulo sys
import logging # Importa o módulo logging
import argparse # Importa o módulo argparse
import uuid # Importa o módulo uuid

# Importa o módulo messaging_rabbit
from src.services.messaging_rabbit import (    
    new_job,
    publish,
    TRANSCRIBE_QUEUE,
    declare_infraestructure,
)

# Importa o módulo initialize_job 
from src.services.state_manager import initialize_job

# Configuração do logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Força o flush do stdout para garantir que os prints apareçam
    sys.stdout.reconfigure(line_buffering=True)
    
    print("\n" + "="*60)
    print("=== CORTAI BACKEND — JOB LAUNCHER ===")
    print("="*60 + "\n")
    sys.stdout.flush() # Força o flush do stdout para garantir que os prints apareçam

    # Garante que as filas/dead-letter estão prontas antes de publicar qualquer job
    log.info("Inicializando infraestrutura de filas...")
    declare_infraestructure() # 
    log.info("Infraestrutura pronta!\n")
    sys.stdout.flush() 

    # Parse de argumentos de linha de comando
    parser = argparse.ArgumentParser(description='CortAI Job Launcher')
    parser.add_argument('--url', type=str, help='URL do vídeo para processar')
    args = parser.parse_args()

    # Tenta obter URL de argumentos, variável de ambiente ou input
    url = args.url or os.getenv('VIDEO_URL')

    # Se a URL não for fornecida, solicita ao usuário
    if not url:
        print("Por favor, insira a URL do vídeo (ex: https://youtube.com/...): ", end="", flush=True)
        try:
            # Tenta obter a URL do input do usuário
            url = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[ERRO] Input cancelado ou não disponível.")
            print("Use: docker-compose run --rm backend python main.py --url <URL>")
            sys.exit(1) # Sai do programa
    
    if not url:
        print("\n[ERRO] A URL do vídeo não pode ser vazia.")
        print("Use: docker-compose run --rm backend python main.py --url <URL>")
        sys.exit(1) # Sai do programa

    # Gera um job_id único automaticamente
    job_id = uuid.uuid4().hex[:12]

    print(f"\n→ Criando job: {job_id}")
    print(f"→ URL: {url}\n")
    sys.stdout.flush() # Força o flush do stdout para garantir que os prints apareçam

    # Inicializa o job no Redis
    initialize_job(job_id, url)

    # Cria e publica a mensagem
    msg = new_job(
        step="transcribe",
        job_id=job_id,
        payload={"url": url}
    )

    # Publica a mensagem na fila
    publish(TRANSCRIBE_QUEUE, msg)

    print("\n" + "="*60)
    print(f"[OK] Job '{job_id}' enviado para a fila transcribe_queue.")
    print("="*60 + "\n")
    sys.stdout.flush() 
