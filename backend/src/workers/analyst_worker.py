"""
Worker responsável pela etapa de análise.
Consome jobs da fila 'analyse_queue' e publica resultados em 'edit_queue'.
"""

import os  # Importa o módulo os
import json  # Importa o módulo json
import logging  # Importa o módulo logging

from src.services.state_manager import update_job_state, JobStatus  # Atualiza o estado do job
from src.services.messaging_rabbit import (
    consume,
    publish,
    new_job,
    ANALYSE_QUEUE,
    EDIT_QUEUE
)

# Importa o novo agente analista baseado em JSON estruturado (Pydantic)
from src.agents.analyst import AnalystAgent

# Configuração do logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("analyst_worker")

# --------------------------------------------------------------------------------------------------------------------------------------

def handle_analyst(message: dict):
    """
    Função de callback para processar mensagens da fila 'analyse_queue'.
    """

    # Extrai os dados do job
    job_id = message["job_id"]
    payload = message["payload"]

    transcription_path = payload["transcription_path"]
    video_path = payload["video_path"]

    print("\n" + "=" * 60)
    print(f"[ANALYST] Processando job: {job_id}")
    print(f"Transcrição: {transcription_path}")
    print("=" * 60)

    # Atualiza o estado inicial
    update_job_state(job_id, JobStatus.PROCESSING, "analyse", {
        "transcription_path": transcription_path
    })

    # Caminho onde o resultado será salvo
    highlight_path = f"/app/data/highlights/{job_id}.json"
    os.makedirs(os.path.dirname(highlight_path), exist_ok=True)

    # Carrega a transcrição
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription_json = json.load(f)
    except Exception as e:
        msg = f"Erro ao carregar transcrição: {str(e)}"
        log.exception(msg)
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed", {"error": msg})
        return

    # Recupera o texto
    texto = transcription_json.get("text", "").strip()
    if not texto:
        msg = "Transcrição vazia ou sem campo 'text'."
        log.error(msg)
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed", {"error": msg})
        return

    # Executa o novo agente analista (LLM com JSON estruturado)
    agent = AnalystAgent()

    try:
        highlight_output, error = agent.run(texto)
    except Exception as e:
        # Erro crítico inesperado no agente
        msg = f"Erro crítico ao executar AnalystAgent: {str(e)}"
        log.exception(msg)
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed", {"error": msg})
        return

    # Se o LLM retornou erro validado pelo próprio agente
    if error:
        msg = f"Falha na análise: {error}"
        log.error(msg)
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed", {"error": msg})
        return

    # Converte Pydantic → dict
    highlight_dict = highlight_output.dict()

    # Salva JSON de highlight
    try:
        with open(highlight_path, "w", encoding="utf-8") as f:
            json.dump(highlight_dict, f, indent=4, ensure_ascii=False)
        print(f"[OK] Análise concluída e salva em: {highlight_path}")
    except Exception as e:
        msg = f"Erro ao salvar highlight JSON: {str(e)}"
        log.exception(msg)
        update_job_state(job_id, JobStatus.FAILED, "analyse_failed", {"error": msg})
        return

    # Cria payload para a próxima etapa
    next_payload = {
        "highlight_path": highlight_path,
        "video_path": video_path
    }

    # Cria mensagem para o editor
    next_msg = new_job(
        step="edit",
        payload=next_payload,
        job_id=job_id
    )

    # Publica na fila
    publish(EDIT_QUEUE, next_msg)
    print(f"[→] Job {job_id} enviado para edição.\n")

    # Atualiza o estado
    update_job_state(job_id, JobStatus.PROCESSING, "edit", next_payload)

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n=== WORKER ANALYST INICIADO ===")
    print(f"Escutando fila: {ANALYSE_QUEUE}")
    print("Aguardando jobs...\n")

    # Inicia o consumidor da fila
    consume(ANALYSE_QUEUE, handle_analyst)
