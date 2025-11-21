import os  # Acessa variáveis e recursos do Sistema Operacional 
import json  # Permite ler/escrever objetos no formato JSON
import uuid  # Usado para gerar identificadores únicos para cada job
import logging  # Exibe logs estruturados no terminal (INFO, WARNING, ERROR)

# Tipagem estática para maior clareza e ajuda do editor
from typing import Callable, Dict, Any

# Carrega variáveis do arquivo .env
from dotenv import load_dotenv

# Cliente oficial do RabbitMQ para Python
import pika

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --------------------------------------------------------------------------------------------------------------------------------------

"""
Sistema de mensageria para pipeline de processamento de vídeo.
Usa RabbitMQ para comunicação assíncrona entre os serviços distribuídos
(coletor -> transcritor -> analista -> editor -> finalização).
"""

# Configurações gerais
# URL de conexão com RabbitMQ. Se não estiver definida no .env, usa localhost.
RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Filas do pipeline
COLLECT_QUEUE = "collect_queue"          # Fila para coletar o stream/vídeo
DEAD_LETTER_EXCHANGE = "dlx"             # Exchange de Dead Letter (erros)
DEAD_LETTER_QUEUE = "dead_letter_queue"  # Fila onde mensagens quebradas são enviadas
TRANSCRIBE_QUEUE = "transcribe_queue"    # Transcrição (Whisper)
ANALYSE_QUEUE = "analyse_queue"          # Análise semântica (LLM)
EDIT_QUEUE = "edit_queue"                # Edição (FFmpeg / MoviePy)
COMPLETED_QUEUE = "completed_queue"      # Conclusão do processo

# Configuração global dos logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("messaging")

# --------------------------------------------------------------------------------------------------------------------------------------

def get_connection():
    """
    Estabelece uma conexão com o servidor RabbitMQ.
    Usa BlockingConnection (síncrona), que é simples e adequada para workers.

    Implementa um sistema de retry com tentativas e tempo de espera.

    Returns:
        pika.BlockingConnection: Conexão ativa com RabbitMQ
    """

    # Configura parâmetros de conexão
    params = pika.URLParameters(RABBIT_URL)

    # Configuração de retry
    max_retries = 10
    retry_delay = 5  # segundos

    # Tenta estabelecer conexão com RabbitMQ
    for attempt in range(max_retries):
        try:
            # Tenta estabelecer conexão
            log.info(f"Tentando conectar ao RabbitMQ (Tentativa {attempt + 1}/{max_retries})...")
            connection = pika.BlockingConnection(params)

            # Conexão estabelecida
            log.info("Conexão com RabbitMQ estabelecida com sucesso.")
            return connection

        # Caso de falha
        except pika.exceptions.AMQPConnectionError as e:
            log.warning(f"Falha na conexão: {e}. Aguardando {retry_delay}s para tentar novamente.")

            # Verifica se ainda há tentativas restantes
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                log.error("Falha ao conectar ao RabbitMQ após várias tentativas.")
                raise e

# --------------------------------------------------------------------------------------------------------------------------------------

def declare_infraestructure():
    """
    Cria todas as filas necessárias no RabbitMQ, incluindo:
    - Filas principais
    - DLQ (Dead Letter Queue)
    - Dead Letter Exchange

    A operação é idempotente — executar várias vezes não causa erros.
    """

    # Estabelece conexão
    conn = get_connection()

    # Cria canal
    ch = conn.channel()

    # Declara exchange de Dead Letter
    ch.exchange_declare(exchange=DEAD_LETTER_EXCHANGE, exchange_type='fanout', durable=True)

    # Declara fila de Dead Letter
    ch.queue_declare(queue=DEAD_LETTER_QUEUE, durable=True)

    # Liga exchange -> fila DLQ
    ch.queue_bind(exchange=DEAD_LETTER_EXCHANGE, queue=DEAD_LETTER_QUEUE)

    # Argumentos que linkam filas principais ao DLQ
    dlq_args = {
        "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
        "x-dead-letter-routing-key": ""
    }

    # Declara filas principais com DLQ configurada
    ch.queue_declare(queue=COLLECT_QUEUE, durable=True, arguments=dlq_args) # durable=True garante que a fila persista mesmo se o RabbitMQ reiniciar
    ch.queue_declare(queue=TRANSCRIBE_QUEUE, durable=True, arguments=dlq_args)
    ch.queue_declare(queue=ANALYSE_QUEUE, durable=True, arguments=dlq_args)
    ch.queue_declare(queue=EDIT_QUEUE, durable=True, arguments=dlq_args)

    # Essa não precisa de DLQ — é uma fila terminal
    ch.queue_declare(queue=COMPLETED_QUEUE, durable=True)

    log.info("Infraestrutura de filas verificada e pronta (incluindo DLQ).")
    conn.close()

# --------------------------------------------------------------------------------------------------------------------------------------

def new_job(step: str, payload: Dict[str, Any], job_id: str | None = None) -> Dict[str, Any]:
    """
    Cria uma mensagem padronizada ('job envelope').

    Args:
        step: Nome da etapa atual do pipeline (ex: 'transcribe')
        payload: Dados necessários para o worker
        job_id: ID externo. Se None, o sistema gera automaticamente.

    Returns:
        dict: Mensagem normalizada com job_id, step e payload
    """

    # Gera um ID único para o job 
    unique_job_id = job_id or uuid.uuid4().hex[:12]

    # Retorna o job normalizado
    return {
        "job_id": unique_job_id,
        "step": step,
        "payload": payload
    }

# --------------------------------------------------------------------------------------------------------------------------------------

def publish(queue: str, message: Dict[str, Any]):
    """
    Publica uma mensagem em uma fila RabbitMQ.

    - Conecta
    - Serializa o JSON
    - Publica com persistência (delivery_mode=2)
    - Fecha a conexão

    Args:
        queue: Fila destino
        message: Dicionário padronizado do job
    """

    conn = get_connection()

    # Abre um canal
    ch = conn.channel()

    # Serializa o JSON 
    body_json = json.dumps(message)

    # Publica a mensagem
    ch.basic_publish(
        exchange="",              # Roteamento direto para a fila
        routing_key=queue,        # Fila de destino
        body=body_json,           # Corpo da mensagem
        properties=pika.BasicProperties(
            delivery_mode=2      # Persistência da mensagem (salva em disco)
        )
    )

    log.info(f"📤 [PUBLISH] Job {message['job_id']} enviado para -> {queue}")
    conn.close()

# --------------------------------------------------------------------------------------------------------------------------------------

def consume(queue: str, handler: Callable[[Dict[str, Any]], None]):
    """
    Inicia um consumidor que escuta uma fila específica.

    - Recebe mensagens
    - Desserializa JSON
    - Executa o handler fornecido
    - Dá ACK se sucesso
    - Dá NACK com requeue=False se erro → mensagem vai para DLQ

    Args:
        queue: Nome da fila a escutar
        handler: Função que processará cada mensagem
    """

    # Conecta ao RabbitMQ
    conn = get_connection()

    # Abre um canal
    ch = conn.channel()

    # Worker processa apenas uma mensagem por vez
    ch.basic_qos(prefetch_count=1)

    # Define a função de callback
    def _callback(ch, method, props, body):
        """
        Função chamada automaticamente quando uma mensagem chega na fila.
        """

        try:
            try:
                # Desserializa o JSON
                msg = json.loads(body.decode())
            except json.JSONDecodeError:
                # Se a mensagem for inválida, envia para DLQ
                log.error(f"Mensagem inválida recebida na fila {queue} — enviando para DLQ")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # Execução da lógica do worker
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            log.exception(f"Erro crítico ao processar mensagem na fila {queue}:")
            # Se houver erro, envia para DLQ
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False  # Não volta para a fila principal → vai para DLQ
            )

    # Registra o consumidor
    ch.basic_consume(queue=queue, on_message_callback=_callback)

    log.info(f"[CONSUMER] Aguardando mensagens na fila: {queue}...")

    # Loop infinito ouvindo mensagens
    ch.start_consuming()

