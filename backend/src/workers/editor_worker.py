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
    output_video_path = f"/app/data/jobs/{job_id}/highlights/{job_id}_highlight.mp4"

    # Garante que o diretório existe
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    try:
        # --- Short-term mitigation: esperar pelo arquivo de vídeo se ele ainda não existir ---
        MAX_VIDEO_WAIT_RETRIES = 5
        VIDEO_WAIT_DELAY = 2  # segundos

        if not os.path.exists(video_path):
            log.warning(f"[{job_id}] video_path não encontrado: {video_path}. Aguardando até {MAX_VIDEO_WAIT_RETRIES*VIDEO_WAIT_DELAY}s...")
            for attempt in range(1, MAX_VIDEO_WAIT_RETRIES + 1):
                if os.path.exists(video_path):
                    log.info(f"[{job_id}] video_path encontrado na tentativa {attempt}.")
                    break
                log.info(f"[{job_id}] Tentativa {attempt}/{MAX_VIDEO_WAIT_RETRIES}: aguardando {VIDEO_WAIT_DELAY}s para o arquivo aparecer...")
                time.sleep(VIDEO_WAIT_DELAY)

        if not os.path.exists(video_path):
            log.error(f"[{job_id}] video_path ainda não encontrado após tentativas: {video_path}")
            update_job_state(job_id, JobStatus.FAILED, "edit_missing_input")
            return

        # Prepara o highlight JSON no formato esperado pelo editor
        # O Analyst pode retornar um JSON simples com chaves: highlight_inicio_segundos, highlight_fim_segundos, resposta_bruta
        # O executar_agente_editor espera {'highlights': [{ 'start':..., 'end':..., 'summary':..., 'score':... }, ...]}
        try:
            with open(highlight_path, 'r', encoding='utf-8') as hf:
                highlight_data = json.load(hf)
        except Exception as e:
            log.exception(f"[{job_id}] Falha ao ler highlight_path {highlight_path}: {e}")
            update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
            return

        # Normaliza para o formato do editor
        converted = None
        if isinstance(highlight_data, dict) and "highlights" in highlight_data:
            converted = highlight_data
        elif isinstance(highlight_data, list):
            converted = {"highlights": highlight_data}
        elif isinstance(highlight_data, dict) and all(k in highlight_data for k in ["highlight_inicio_segundos", "highlight_fim_segundos"]):
            start = float(highlight_data.get("highlight_inicio_segundos", 0))
            end = float(highlight_data.get("highlight_fim_segundos", 60))
            summary = highlight_data.get("resposta_bruta", "")
            converted = {"highlights": [{"start": start, "end": end, "summary": summary, "score": 0}]}
        else:
            log.error(f"[{job_id}] Formato de highlight desconhecido: {type(highlight_data)}")
            update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
            return

        # Escreve JSON convertido em arquivo temporário dentro do diretório do job
        output_dir = os.path.dirname(output_video_path)
        os.makedirs(output_dir, exist_ok=True)
        converted_highlight_path = os.path.join(output_dir, "highlight.json")
        try:
            with open(converted_highlight_path, 'w', encoding='utf-8') as cf:
                json.dump(converted, cf, ensure_ascii=False, indent=4)
        except Exception as e:
            log.exception(f"[{job_id}] Falha ao escrever highlight convertido: {e}")
            update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
            return

        # Executa o agente editor (usa output_dir e recebe lista de clips)
        try:
            result_paths = executar_agente_editor(
                highlight_json=converted_highlight_path,
                input_video=video_path,
                output_dir=output_dir
            )
        except FileNotFoundError as fnf:
            # Se o arquivo sumiu entre a verificação e a execução, tenta novamente uma vez
            log.warning(f"[{job_id}] FileNotFoundError durante execução do editor: {fnf}. Tentando aguardar/reenviar...")
            time.sleep(VIDEO_WAIT_DELAY)
            if not os.path.exists(video_path):
                log.error(f"[{job_id}] video_path ainda ausente após espera: {video_path}")
                update_job_state(job_id, JobStatus.FAILED, "edit_missing_input")
                return
            # segunda tentativa
            try:
                result_paths = executar_agente_editor(
                    highlight_json=converted_highlight_path,
                    input_video=video_path,
                    output_dir=output_dir
                )
            except Exception as e:
                log.exception(f"[{job_id}] Falha na segunda tentativa do editor: {e}")
                update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
                return

        # Normaliza o resultado para um único caminho (first clip)
        result_path = None
        if isinstance(result_paths, list) and result_paths:
            result_path = result_paths[0]
        elif isinstance(result_paths, str):
            result_path = result_paths
        else:
            result_path = None
    except Exception as e:
        # Registra o erro e marca falha crítica sem levantar exceção para não interromper o loop de consumo
        log.exception(f"[{job_id}] Erro crítico durante edição: {e}")
        update_job_state(job_id, JobStatus.FAILED, "edit_critical_error")
        return

    # Se a edição falhar
    if not result_path:
        print(f"[ERRO] Falha ao editar o vídeo no job {job_id}.")
        # Atualiza o estado do job
        update_job_state(job_id, JobStatus.FAILED, "edit_failed")
        return # Retorna para o loop

    print(f"[OK] Highlight gerado em: {result_path}")

    # Cria o payload para a próxima etapa
    completed_payload = {
        "final_video_path": result_path,
        "original_video_path": video_path,
        "highlight_json_path": highlight_path
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
