"""
CortAI - Script Principal Interativo
Permite processar vídeos gravados ou live streams via input no terminal.
Detecta automaticamente o tipo de conteúdo e roteia para o worker apropriado.
"""

import os # Importa o módulo os
import sys # Importa o módulo sys
import logging # Importa o módulo logging
import uuid # Importa o módulo uuid
import re # Importa o módulo re

# Importa o módulo messaging_rabbit
from src.services.messaging_rabbit import (
    new_job,
    publish,
    TRANSCRIBE_QUEUE,
    COLLECT_QUEUE,
    declare_infraestructure,
)

# Importa o módulo initialize_job
from src.services.state_manager import initialize_job

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("main")

# --------------------------------------------------------------------------------------------------------------------------------------

def detect_content_type(url: str) -> str:
    """
    Detecta se a URL é um vídeo gravado ou uma live stream.
    
    Args:
        url: URL a ser analisada
        
    Returns:
        'stream' para live streams ou URLs HLS/m3u8
        'youtube' para URLs do YouTube (requer confirmação do usuário)
        'video' para vídeos gravados de outras plataformas
    """
    url_lower = url.lower()
    
    # Detecta streams HLS
    if '.m3u8' in url_lower or 'manifest' in url_lower:
        return 'stream'
    
    # Detecta YouTube (pode ser live ou vídeo gravado)
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    
    # Detecta Twitch (stream)
    if 'twitch.tv' in url_lower:
        return 'stream'
    
    # Por padrão, trata como vídeo gravado
    return 'video'

# --------------------------------------------------------------------------------------------------------------------------------------

def print_banner():
    """
    Imprime o banner do CortAI
    """
    print("\n" + "="*70)
    print("🎬 CORTAI - Processamento Inteligente de Vídeos e Streams")
    print("="*70)
    print()

# --------------------------------------------------------------------------------------------------------------------------------------

def get_url_from_user() -> str:
    """
    Solicita URL do usuário via input interativo.
    
    Returns:
        URL fornecida pelo usuário
    """
    print("📺 Insira a URL do conteúdo:")
    print()
    print("   Exemplos de vídeos gravados:")
    print("   - YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print()
    print("   Exemplos de live streams:")
    print("   - Stream HLS: https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
    print("   - YouTube Live: https://youtube.com/watch?v=...")
    print("   - Twitch: https://twitch.tv/channel")
    print()
    
    try:
        url = input("URL: ").strip()
        return url
    except (EOFError, KeyboardInterrupt):
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0) # Sai do programa

# --------------------------------------------------------------------------------------------------------------------------------------

def ask_youtube_type() -> str:
    """
    Pergunta ao usuário se o conteúdo do YouTube é live stream ou vídeo gravado.
    
    Returns:
        'stream' para live streams
        'video' para vídeos gravados
    """
    print()
    print("🎥 TIPO DE CONTEÚDO DO YOUTUBE")
    print("-" * 70)
    print("Este link é:")
    print("  [1] Vídeo gravado (padrão)")
    print("  [2] Live stream ao vivo")
    print()
    
    try:
        choice = input("Escolha uma opção: ").strip()
        
        if choice == '2':
            return 'stream'
        else:
            return 'video'
    except (EOFError, KeyboardInterrupt):
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0)

# --------------------------------------------------------------------------------------------------------------------------------------

def get_stream_parameters() -> dict:
    """
    Solicita parâmetros específicos para processamento de streams.
    
    Returns:
        Dicionário com segment_duration e max_duration
    """
    print()
    print("⚙️ CONFIGURAÇÃO DO STREAM")
    print("-" * 70)
    
    # Duração do segmento
    print("⏱️ Duração de cada segmento (em segundos):")
    print("   Padrão: 30 segundos")
    segment_input = input("Duração do segmento [30]: ").strip()
    segment_duration = int(segment_input) if segment_input else 30
    
    print()
    
    # Duração máxima
    print("⏱️  Duração máxima da captura (em segundos):")
    print("   Padrão: 120 segundos (2 minutos)")
    max_input = input("Duração máxima: ").strip()
    max_duration = int(max_input) if max_input else 120
    
    return {
        'segment_duration': segment_duration,
        'max_duration': max_duration
    }

# --------------------------------------------------------------------------------------------------------------------------------------

def process_video(url: str, job_id: str):
    """
    Processa um vídeo gravado (YouTube, etc).
    Publica job na fila transcribe_queue.
    
    Args:
        url: URL do vídeo
        job_id: ID único do job
    """
    print()
    print("="*70)
    print("📹 MODO: Vídeo Gravado")
    print("="*70)
    print(f"🆔 Job ID: {job_id}")
    print(f"🔗 URL: {url}")
    print()
    print("📋 Fluxo de processamento:")
    print("   1. Download do vídeo")
    print("   2. Transcrição com Whisper")
    print("   3. Análise de conteúdo")
    print("   4. Geração de highlights")
    print("="*70)
    
    # Inicializa o job no Redis
    initialize_job(job_id, url)
    
    # Cria e publica a mensagem
    msg = new_job(
        step="transcribe",
        job_id=job_id,
        payload={"url": url}
    )
    
    # Publica na fila de transcrição
    publish(TRANSCRIBE_QUEUE, msg)
    
    print()
    print("✅ Job publicado com sucesso!")
    print()
    print("🔍 Monitore o progresso:")
    print(f"   docker-compose logs -f transcriber-worker")
    print()
    print("📁 Arquivos serão salvos em:")
    print(f"   Vídeo: backend/data/videos/{job_id}.mp4")
    print(f"   Transcrição: backend/data/jobs/{job_id}/transcriptions/{job_id}.json")
    print("="*70)

# --------------------------------------------------------------------------------------------------------------------------------------

def process_stream(url: str, job_id: str, params: dict):
    """
    Processa uma live stream.
    Publica job na fila collect_queue.
    
    Args:
        url: URL do stream
        job_id: ID único do job
        params: Parâmetros do stream (segment_duration, max_duration)
    """
    print()
    print("="*70)
    print("📡 MODO: Live Stream")
    print("="*70)
    print(f"🆔 Job ID: {job_id}")
    print(f"🔗 URL: {url}")
    print(f"⏱️  Segmentos de: {params['segment_duration']}s")
    print(f"⏱️  Duração máxima: {params['max_duration']}s")
    print(f"📊 Segmentos esperados: ~{params['max_duration'] // params['segment_duration']}")
    print()
    print("📋 Fluxo de processamento:")
    print("   1. Captura e segmentação do stream")
    print("   2. Transcrição de cada segmento")
    print("   3. Análise de conteúdo")
    print("   4. Geração de highlights")
    print("="*70)
    
    # Inicializa o job no Redis
    initialize_job(job_id, url)
    
    # Cria e publica a mensagem
    msg = new_job(
        step="collect",
        job_id=job_id,
        payload={
            "stream_url": url,
            "segment_duration": params['segment_duration'],
            "max_duration": params['max_duration']
        }
    )
    
    # Publica na fila de coleta
    publish(COLLECT_QUEUE, msg)
    
    print()
    print("✅ Job publicado com sucesso!")
    print()
    print("🔍 Monitore o progresso:")
    print(f"   docker-compose logs -f collector-worker")
    print(f"   docker-compose logs -f transcriber-worker")
    print()
    print("📁 Arquivos serão salvos em:")
    print(f"   backend/data/jobs/{job_id}/")
    print(f"   ├── segments/        (vídeos segmentados)")
    print(f"   ├── transcriptions/  (transcrições JSON)")
    print(f"   ├── analysis/        (análises)")
    print(f"   └── highlights/      (vídeos finais)")
    print()
    print("🌐 RabbitMQ Management:")
    print(f"   http://localhost:15672")
    print(f"   User: cortai | Pass: cortai_password")
    print("="*70)

# --------------------------------------------------------------------------------------------------------------------------------------

def main():
    """
    Função principal do script
    """
    
    # Força o flush do stdout
    sys.stdout.reconfigure(line_buffering=True)
    
    # Imprime banner
    print_banner()
    
    # Inicializa infraestrutura
    log.info("Inicializando infraestrutura de filas...")
    declare_infraestructure()
    log.info("Infraestrutura pronta!\n")
    sys.stdout.flush()
    
    # Obtém URL do usuário
    url = get_url_from_user()
    
    # Valida URL
    if not url:
        print("\n❌ Erro: URL não pode estar vazia!")
        sys.exit(1)
    
    # Detecta tipo de conteúdo
    content_type = detect_content_type(url)
    
    # Se for YouTube, pergunta ao usuário o tipo
    if content_type == 'youtube':
        content_type = ask_youtube_type()
    
    # Gera job_id único
    job_id = uuid.uuid4().hex[:12]
    
    # Processa baseado no tipo
    if content_type == 'stream':
        # Solicita parâmetros do stream
        params = get_stream_parameters()
        
        # Confirmação
        print()
        confirmar = input("Deseja processar este stream? (s/N): ").strip().lower()
        if confirmar not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário.")
            sys.exit(0)
        
        # Processa stream
        process_stream(url, job_id, params)
    else:
        # Confirmação
        print()
        confirmar = input("Deseja processar este vídeo? (s/N): ").strip().lower()
        if confirmar not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário.")
            sys.exit(0)
        
        # Processa vídeo
        process_video(url, job_id)
    
    print()

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0) # Sai do programa
    except Exception as e:
        log.exception(f"Erro ao processar: {e}")
        sys.exit(1) # Sai do programa