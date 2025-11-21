"""
Worker responsável pela etapa de análise.
Consome jobs da fila 'analyse_queue' e publica resultados em 'edit_queue'.
"""

import os # Importa o módulo os
import json # Importa o módulo json
import logging # Importa o módulo logging
from src.services.state_manager import update_job_state, JobStatus # Importa as classes update_job_state e JobStatus

# Importa as funções consume, publish, new_job, ANALYSE_QUEUE e EDIT_QUEUE do módulo messaging_rabbit
from src.services.messaging_rabbit import (
    consume,
    publish,
    new_job,
    ANALYSE_QUEUE,
    EDIT_QUEUE
)

# Importa a função executar_agente_analista do módulo analyst
from src.agents.analyst import executar_agente_analista

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("analyst_worker")

# --------------------------------------------------------------------------------------------------------------------------------------

def handle_analyst(message: dict):
    """
    Função de callback para processar mensagens da fila 'analyse_queue'.
    """

    # Extrai os dados do job
    job_id = message["job_id"]
    payload = message["payload"]

    # Extrai os dados do payload
    transcription_path = payload["transcription_path"]
    video_path = payload["video_path"]

    # Imprime os dados do job
    print("\n" + "="*60)
    print(f"[ANALYST] Processando job: {job_id}")
    print(f"Transcrição: {transcription_path}")
    print("="*60)

    # Atualiza o estado do job
    update_job_state(job_id, JobStatus.PROCESSING, "analyse", {"transcription_path": transcription_path})

    # Cria o diretório para os highlights
    highlight_path = f"/app/data/highlights/{job_id}.json"

    # Garante que o diretório existe
    os.makedirs(os.path.dirname(highlight_path), exist_ok=True)

    try:
        # Executa o agente analista
        highlight = executar_agente_analista(
            input_json=transcription_path,
            output_json=highlight_path
        )
    except Exception as e:
        # Registra o erro
        log.exception(f"[{job_id}] Erro crítico durante análise: {e}")
        raise # Releva o erro para o tratamento global

    # Se a análise falhar
    if highlight is None:
        print(f"[ERRO] Falha ao analisar a transcrição no job {job_id}.")
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed") # Atualiza o estado do job
        return

    print(f"[OK] Análise concluída e salva em: {highlight_path}")

    # Cria o payload para a próxima etapa
    next_payload = {
        "highlight_path": highlight_path,
        "video_path": video_path
    }

    # Cria a mensagem para a próxima etapa
    next_msg = new_job(
        step="edit",
        payload=next_payload,
        job_id=job_id
    )

    # Publica a mensagem na fila
    publish(EDIT_QUEUE, next_msg)
    print(f"[→] Job {job_id} enviado para edição.\n")

    # Atualiza o estado do job
    update_job_state(job_id, JobStatus.PROCESSING, "edit", next_payload)

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Inicia o worker
    print("\n=== WORKER ANALYST INICIADO ===")
    print(f"Escutando fila: {ANALYSE_QUEUE}")
    print("Aguardando jobs...\n")

    # Consume a fila
    consume(ANALYSE_QUEUE, handle_analyst)
