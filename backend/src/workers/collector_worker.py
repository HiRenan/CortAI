"""
Worker responsável pela etapa de coleta de streams.
Consome jobs da fila 'collect_queue' e publica segmentos em 'transcribe_queue'.
"""

import os  # Importa o módulo os
import logging  # Importa o módulo logging
from src.services.state_manager import update_job_state, initialize_job, JobStatus  # Importa as classes update_job_state, initialize_job e JobStatus

# Importa as funções consume, publish, new_job, COLLECT_QUEUE e TRANSCRIBE_QUEUE do módulo messaging_rabbit
from src.services.messaging_rabbit import (
    consume,
    publish,
    new_job,
    declare_infraestructure,
    COLLECT_QUEUE,
    TRANSCRIBE_QUEUE
)

# Importa a função executar_agente_coletor do módulo collector_streams
from src.agents.collector_streams import executar_agente_coletor

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("collector_worker")

# --------------------------------------------------------------------------------------------------------------------------------------

def handle_collector(message: dict):
    """
    Handler que processa mensagens da fila de coleta de streams.
    
    Args:
        message(dict): Mensagem contendo job_id e payload com a URL do stream
    """

    try:
        # Extrai os dados do job
        job_id = message.get("job_id")

        # Extrai os dados do payload
        payload = message.get("payload", {})
        stream_url = payload.get("stream_url")
        segment_duration = payload.get("segment_duration", 30)  # Padrão: 30 segundos
        max_duration = payload.get("max_duration", 300)  # Padrão: 5 minutos

        # Verifica se o job_id e stream_url existem
        if not job_id:
            log.error("Mensagem sem job_id!")
            return

        # Verifica se a URL do stream existe
        if not stream_url:
            log.error(f"Job {job_id} sem URL do stream!")
            # Atualiza o estado do job
            update_job_state(job_id, JobStatus.FAILED, "collect_invalid_url", {"error": "URL do stream não fornecida"})
            return  # Retorna para o loop

        # Imprime os dados do job
        log.info("\n" + "="*60)
        log.info(f"[COLLECTOR] Processando job: {job_id}")
        log.info(f"Stream URL: {stream_url}")
        log.info(f"Duração do segmento: {segment_duration}s")
        log.info(f"Duração máxima: {max_duration}s")
        log.info("="*60)

        # Atualiza estado para PROCESSING
        update_job_state(job_id, JobStatus.PROCESSING, "collect", {"stream_url": stream_url})

        # Define o diretório de saída para os segmentos (organizado por job_id)
        output_dir = f"/app/data/jobs/{job_id}/segments"

        # Garante que o diretório existe
        os.makedirs(output_dir, exist_ok=True)

        # Imprime o diretório de saída
        log.info(f"Diretório de saída: {output_dir}")
        log.info("Iniciando captura e segmentação do stream...")

        # Executa a coleta do stream
        try:
            result = executar_agente_coletor(
                stream_url=stream_url,
                output_dir=output_dir,
                segment_duration=segment_duration,
                max_duration=max_duration
            )
        except Exception as e:
            # Registra o erro
            log.exception(f"[{job_id}] Erro crítico durante coleta: {e}")
            # Atualiza o estado do job
            update_job_state(
                job_id,
                JobStatus.FAILED,
                "collect_critical_error",
                {"error": str(e)}
            )
            raise  # Re-raise para que a mensagem vá para DLQ

        # Verifica se a coleta foi bem-sucedida
        if result is None or result.get("status") != "sucesso":
            # Registra o erro
            log.error(f"[{job_id}] Falha ao coletar o stream.")
            # Atualiza o estado do job
            update_job_state(job_id, JobStatus.FAILED, "collect_failed", {"error": "Coleta retornou None ou falhou"})
            return

        log.info(f"[OK] Coleta concluída! Total de segmentos: {result['segment_count']}")

        # Publica cada segmento na fila de transcrição
        segment_paths = result.get("segment_paths", [])
        
        if not segment_paths:
            log.warning(f"[{job_id}] Nenhum segmento foi gerado.")
            update_job_state(job_id, JobStatus.FAILED, "collect_no_segments", {"error": "Nenhum segmento gerado"})
            return

        # Atualiza estado indicando que está enviando segmentos para transcrição
        update_job_state(
            job_id, 
            JobStatus.PROCESSING, 
            "collect_publishing_segments", 
            {"segment_count": len(segment_paths)}
        )

        # Publica cada segmento individualmente na fila de transcrição
        for idx, segment_path in enumerate(segment_paths):
            # Prepara payload para transcrição
            transcribe_payload = {
                "segment_path": segment_path,
                "segment_index": idx,
                "total_segments": len(segment_paths),
                "parent_job_id": job_id  # Mantém referência ao job original
            }

            # Cria mensagem para fila de transcrição
            # Cada segmento terá seu próprio sub-job_id
            segment_job_id = f"{job_id}_seg{idx:03d}"
            
            # Inicializa o segmento no Redis
            initialize_job(segment_job_id, stream_url)
            
            # Atualiza com metadados do segmento
            update_job_state(segment_job_id, JobStatus.PENDING, "transcribe", {
                "parent_job_id": job_id,
                "segment_index": idx,
                "total_segments": len(segment_paths),
                "segment_path": segment_path
            })
            
            # Cria mensagem para fila de transcrição
            transcribe_msg = new_job(
                step="transcribe",
                payload=transcribe_payload,
                job_id=segment_job_id
            )

            # Publica na fila de transcrição
            publish(TRANSCRIBE_QUEUE, transcribe_msg)
            log.info(f"[→] Segmento {idx+1}/{len(segment_paths)} enviado para transcrição (job: {segment_job_id})")

        log.info(f"[✓] Todos os {len(segment_paths)} segmentos do job {job_id} foram enviados para transcrição.")

        # Atualiza estado final da coleta
        update_job_state(
            job_id, 
            JobStatus.PROCESSING, 
            "transcribe", 
            {
                "segments_published": len(segment_paths),
                "output_dir": output_dir
            }
        )

    except KeyError as e:
        # Registra o erro
        log.error(f"Erro ao processar mensagem: campo faltando - {e}")
        import json
        log.error(f"Mensagem recebida: {json.dumps(message, indent=2)}")
    except Exception as e:
        log.exception(f"Erro inesperado ao processar mensagem: {e}")
        raise  # Re-raise para que a mensagem vá para DLQ

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Inicia o worker
    log.info("\n=== WORKER COLLECTOR INICIADO ===")
    
    # Garante que a infraestrutura de filas existe
    log.info("Verificando infraestrutura de filas...")
    declare_infraestructure()
    log.info("Infraestrutura verificada!\n")
    
    log.info(f"Escutando fila: {COLLECT_QUEUE}")
    log.info("Aguardando jobs...\n")

    # Consume a fila
    consume(COLLECT_QUEUE, handle_collector)
