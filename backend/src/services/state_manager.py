import os  # Permite acessar variáveis de ambiente e interagir com o SO
import json  # Usado para serializar e desserializar dados em formato JSON
import logging  # Biblioteca padrão para registro de logs
import time # Permite adicionar delay entre tentativas
from typing import Dict, Any  # Tipagem
from dotenv import load_dotenv # Carrega variáveis de ambiente do arquivo .env
import redis # Cliente oficial do Redis para Python

load_dotenv()

# URL de conexão com Redis. Se não estiver definida no .env, usa localhost.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configuração global dos logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("state_manager")

# Cliente Redis global, reutilizável
_redis_client: redis.Redis | None = None

# --------------------------------------------------------------------------------------------------------------------------------------

def _connect_redis(retries: int = 5, delay: int = 2) -> redis.Redis | None:
    """
    Realiza tentativas de conexão com o Redis e retorna o cliente válido.
    """

    # Tenta conectar ao Redis com retries tentativas e delay entre tentativas
    for attempt in range(1, retries + 1):
        try:
            # Tenta conectar ao Redis
            client = redis.from_url(REDIS_URL, decode_responses=True)

            # Verifica se a conexão foi estabelecida
            client.ping()

            # Registra a conexão
            log.info(f"Conexão com Redis estabelecida em: {REDIS_URL}")
            return client

        except redis.exceptions.ConnectionError as exc:
            # Registra a falha
            log.warning(f"Tentativa {attempt}/{retries} falhou ao conectar no Redis ({exc}).")

            # Verifica se ainda há tentativas restantes
            if attempt < retries:
                time.sleep(delay)

    log.error(f"Não foi possível conectar ao Redis em {REDIS_URL} após {retries} tentativas.")
    return None # Retorna None se não foi possível conectar

# --------------------------------------------------------------------------------------------------------------------------------------

def get_redis_client() -> redis.Redis | None:
    """
    Retorna o cliente Redis reutilizável, conectando sob demanda.
    """

    # Verifica se o cliente já foi conectado
    global _redis_client
    if _redis_client is not None:
        return _redis_client # Retorna o cliente se já foi conectado

    _redis_client = _connect_redis() # Conecta ao Redis
    return _redis_client # Retorna o cliente

# --------------------------------------------------------------------------------------------------------------------------------------

class JobStatus:
    """
    Enumeração de status de job.
    """
    PENDING = "PENDING" 
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# --------------------------------------------------------------------------------------------------------------------------------------

def get_job_key(job_id: str) -> str: 
    """
    Gera a chave para o job no Redis.
    """
    return f"job:{job_id}"

# --------------------------------------------------------------------------------------------------------------------------------------

def initialize_job(job_id: str, url: str):
    """
    Inicializa um job no Redis.
    """

    # Conecta ao Redis 
    client = get_redis_client()
    if client is None:
        log.warning("Redis não conectado. Estado não será persistido.")
        return

    # Inicializa o job no Redis
    initial_state = {
        "job_id": job_id, # ID do job
        "url": url, # URL do job
        "status": JobStatus.PENDING, # Status do job
        "current_step": "START", # Passo atual do job
        "progress": 0, # Progresso do job
        "created_at": os.getenv("CURRENT_TIME") or "unknown" # Data de criação do job
    }

    # Salva o job no Redis
    client.set(get_job_key(job_id), json.dumps(initial_state))
    log.info(f"Job {job_id} inicializado no Redis com status: {JobStatus.PENDING}")

# --------------------------------------------------------------------------------------------------------------------------------------

def update_job_state(job_id: str, status: str, current_step: str, data: Dict[str, Any] = None):
    """
    Atualiza o estado de um job no Redis.
    """

    # Conecta ao Redis
    client = get_redis_client()
    if client is None:
        log.warning("Redis não conectado. Estado não será atualizado.")
        return

    # Atualiza o job no Redis
    key = get_job_key(job_id) 
    current_state_json = client.get(key) # 
    if not current_state_json:
        log.warning(f"Tentativa de atualizar job {job_id}, mas não encontrado no Redis.")
        return

    # Atualiza o job no Redis
    current_state = json.loads(current_state_json)
    current_state["status"] = status
    current_state["current_step"] = current_step

    if data: 
        current_state.update(data) 

    client.set(key, json.dumps(current_state)) # Salva o job no Redis 
    log.info(f"Job {job_id} atualizado. Status: {status}, Passo: {current_step}")

# --------------------------------------------------------------------------------------------------------------------------------------

def get_job_state(job_id: str) -> Dict[str, Any] | None:
    """
    Recupera o estado de um job no Redis.
    """

    # Conecta ao Redis
    client = get_redis_client()
    if client is None:
        log.warning("Redis não conectado. Não é possível recuperar o estado.")
        return None

    # Recupera o job no Redis
    state_json = client.get(get_job_key(job_id))
    if state_json:
        return json.loads(state_json)
    return None # Retorna None se não encontrado