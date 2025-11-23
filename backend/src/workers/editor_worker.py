"""
Worker responsável pela etapa de edição.
Consome jobs da fila 'edit_queue' e publica resultados em 'completed_queue'.
"""

import os # Importa o módulo os
import json # Importa o módulo json
import logging # Importa o módulo logging
import time # Usado para retry/backoff quando o arquivo de vídeo ainda não existir
from src.services.state_manager import update_job_state, JobStatus # Importa as classes update_job_state e JobStatus

# Importa as funções consume, publish, new_job, EDIT_QUEUE e COMPLETED_QUEUE do módulo messaging_rabbit
from src.services.messaging_rabbit import (
    consume,
    publish,
    new_job,
    declare_infraestructure,
    EDIT_QUEUE,
    COMPLETED_QUEUE
)

# Importa a função executar_agente_editor do módulo editor 
from src.agents.editor import executar_agente_editor

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("editor_worker") # Cria o logger

# --------------------------------------------------------------------------------------------------------------------------------------

def handle_editor(message: dict):
    """
    Função de callback para processar mensagens da fila 'edit_queue'.
    """

    # Extrai os dados do job
    job_id = message["job_id"]
    payload = message["payload"]

    # Extrai os dados do payload
    highlight_path = payload["highlight_path"]
    video_path = payload["video_path"]

    # Imprime os dados do job
    print("\n" + "="*60)
    print(f"[EDITOR] Processando job: {job_id}")
    print(f"Highlight: {highlight_path}")
    print("="*60)

    # Atualiza o estado do job
    update_job_state(job_id, JobStatus.PROCESSING, "edit", {"highlight_path": highlight_path})

    # Cria o diretório para o vídeo editado (organizado por job_id)
    output_dir = f"/app/data/jobs/{job_id}/highlights"

    # Garante que o diretório existe
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Executa o agente editor
        result_path = executar_agente_editor(
            highlight_json=highlight_path,
            input_video=video_path,
            output_dir=output_dir
        )
    except Exception as e:
        # Registra o erro e marca falha crítica sem levantar exceção para não interromper o loop de consumo
        log.exception(f"[{job_id}] Erro crítico durante edição: {e}")
        update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
        return

    # Normaliza retorno para lista e primeiro clip
    if isinstance(result_path, list):
        clips_paths = result_path
        final_path = result_path[0] if result_path else None
    else:
        final_path = result_path
        clips_paths = [result_path] if result_path else []

    # Se a edição falhar
    if not final_path:
        print(f"[ERRO] Falha ao editar o vídeo no job {job_id}.")
        # Atualiza o estado do job
        update_job_state(job_id, JobStatus.FAILED, "edit_failed")
        return # Retorna para o loop

    print(f"[OK] Highlight gerado em: {final_path}")

    # Cria o payload para a próxima etapa
    completed_payload = {
        "final_video_path": final_path,
        "original_video_path": video_path,
        "highlight_json_path": highlight_path,
        "clips_paths": clips_paths
    }

    # Cria a mensagem para a próxima etapa
    completed_msg = new_job(
        step="completed",
        payload=completed_payload,
        job_id=job_id
    )

    # Publica a mensagem na fila
    publish(COMPLETED_QUEUE, completed_msg)
    print(f"[→] Job {job_id} enviado para conclusão.\n")

    # Atualiza o estado do job
    update_job_state(job_id, JobStatus.COMPLETED, "completed", completed_payload)

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Inicia o worker
    print("\n=== WORKER EDITOR INICIADO ===")
    
    # Garante que a infraestrutura de filas existe
    print("Verificando infraestrutura de filas...")
    declare_infraestructure()
    print("Infraestrutura verificada!\n")
    
    print(f"Escutando fila: {EDIT_QUEUE}")
    print("Aguardando jobs...\n")

    # Consume a fila
    consume(EDIT_QUEUE, handle_editor)
