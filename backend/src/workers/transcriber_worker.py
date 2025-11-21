"""
Worker responsável pela etapa de:
1) Receber um job da fila 'transcribe_queue'
2) Baixar o vídeo
3) Transcrever usando Whisper
4) Salvar a transcrição em arquivo JSON
5) Publicar na fila 'analyse_queue'
"""

import os # Importa o módulo os
import json # Importa o módulo json
import logging # Importa o módulo logging
from src.services.state_manager import update_job_state, JobStatus # Importa as classes update_job_state e JobStatus

# Importa as funções consume, publish, new_job, TRANSCRIBE_QUEUE e ANALYSE_QUEUE do módulo messaging_rabbit
from src.services.messaging_rabbit import (
    consume,
    publish,
    new_job,
    TRANSCRIBE_QUEUE,
    ANALYSE_QUEUE
)

# Importa a função transcricao_youtube_video do módulo transcriber
from src.agents.transcriber import transcricao_youtube_video

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("transcriber_worker")

# --------------------------------------------------------------------------------------------------------------------------------------

def handle_transcriber(message: dict):
    """
    Handler que processa mensagens da fila de transcrição.
    
    Args:
        message (dict): Mensagem contendo job_id e payload com a URL do vídeo
    """

    try:
        # Extrai os dados do job
        job_id = message.get("job_id")

        # Extrai os dados do payload
        payload = message.get("payload", {})
        url = payload.get("url")

        # Verifica se o job_id e url existem
        if not job_id:
            log.error("Mensagem sem job_id!")
            return

        # Verifica se a URL do vídeo existe
        if not url:
            log.error(f"Job {job_id} sem URL do vídeo!")
            # Atualiza o estado do job
            update_job_state(job_id, JobStatus.FAILED, "transcribe_invalid_url", {"error": "URL não fornecida"})
            return # Retorna para o loop

        # Imprime os dados do job
        log.info("\n" + "="*60)
        log.info(f"[TRANSCRIBER] Processando job: {job_id}")
        log.info(f"URL: {url}")
        log.info("="*60)

        # Atualiza estado para PROCESSING
        update_job_state(job_id, JobStatus.PROCESSING, "transcribe", {"url": url})

        # Define caminhos dos arquivos
        output_path = f"/app/data/transcriptions/{job_id}.json"
        temp_video_path = f"/app/data/videos/{job_id}.mp4"

        # Garante que os diretórios existam
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)

        # Imprime os caminhos dos arquivos
        log.info(f"Arquivo de saída: {output_path}")
        log.info(f"Vídeo temporário: {temp_video_path}")
        log.info("Iniciando download e transcrição...")

        # Executa a transcrição
        try:
            result = transcricao_youtube_video(
                url=url,
                temp_video_path=temp_video_path,
                model_size="base",
                output_json_path=output_path
            )
        except Exception as e:
            # Registra o erro
            log.exception(f"[{job_id}] Erro crítico durante transcrição: {e}")
            # Atualiza o estado do job
            update_job_state(
                job_id,
                JobStatus.FAILED,
                "transcribe_critical_error",
                {"error": str(e)}
            )
            raise  # Re-raise para que a mensagem vá para DLQ

        # Verifica se a transcrição foi bem-sucedida
        if result is None:
            # Registra o erro
            log.error(f"[{job_id}] Falha ao transcrever o vídeo.")
            # Atualiza o estado do job
            update_job_state(job_id, JobStatus.FAILED, "transcribe_failed", {"error": "Transcrição retornou None"})
            return

        log.info(f"[OK] Transcrição concluída e salva em: {output_path}")

        # Prepara payload para próxima etapa
        next_payload = {
            "transcription_path": output_path,
            "video_path": temp_video_path
        }

        # Cria mensagem para fila de análise
        next_msg = new_job(
            step="analyse",
            payload=next_payload,
            job_id=job_id
        )

        # Publica na fila de análise
        publish(ANALYSE_QUEUE, next_msg)
        log.info(f"[→] Job {job_id} enviado para análise.")

        # Atualiza estado
        update_job_state(job_id, JobStatus.PROCESSING, "analyse", next_payload)

    except KeyError as e:
        # Registra o erro
        log.error(f"Erro ao processar mensagem: campo faltando - {e}")
        log.error(f"Mensagem recebida: {json.dumps(message, indent=2)}")
    except Exception as e:
        log.exception(f"Erro inesperado ao processar mensagem: {e}")
        raise  # Re-raise para que a mensagem vá para DLQ

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Inicia o worker
    log.info("\n=== WORKER TRANSCRIBER INICIADO ===")
    log.info(f"Escutando fila: {TRANSCRIBE_QUEUE}")
    log.info("Aguardando jobs...\n")

    # Consume a fila
    consume(TRANSCRIBE_QUEUE, handle_transcriber)
