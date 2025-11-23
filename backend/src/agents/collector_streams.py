import os  # Interage com o Sistema Operacional
import subprocess  # Executa outros programas/comandos do SO
from typing import Dict, Any, Optional, List  # Usada para tipar as funções
import time  # Para controle de tempo
import logging # Importa o módulo logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coletor_streams")

# --------------------------------------------------------------------------------------------------------------------------------------

def _validar_url_stream(url: str) -> bool:
    """
    Valida se a URL do stream é acessível.
    
    Args:
        url (str): URL do stream a ser validado
        
    Returns:
        bool: True se a URL é válida, False caso contrário
    """

    # Verifica se a URL é vazia ou não é uma string
    if not url or not isinstance(url, str):
        return False
    
    # Valida se é uma URL válida (começa com http/https ou é um arquivo local)
    if url.startswith(("http://", "https://", "rtmp://", "rtsp://")) or os.path.exists(url):
        return True
    
    # Caso contrário, retorna False
    return False

# --------------------------------------------------------------------------------------------------------------------------------------

def _extrair_url_stream(url: str) -> Optional[str]:
    """
    Extrai a URL real do stream de uma plataforma (YouTube, Twitch, etc) usando yt-dlp.
    
    Args:
        url (str): URL do vídeo/live
        
    Returns:
        Optional[str]: URL do stream HLS/DASH, ou None se falhar
    """
    try:
        logger.info(f"Extraindo URL do stream de: {url}")
        
        # Comando para extrair a URL do stream
        comando = [
            "yt-dlp",               
            "-f", "best",           # Melhor qualidade disponível
            "-g",                   # Retorna apenas a URL do stream
            url                     
        ]
        
        # Executa o comando
        resultado = subprocess.run(
            comando,
            capture_output=True,  # Captura a saída do comando
            text=True,            # Retorna a saída como string
            timeout=30            # Timeout de 30 segundos
        )
        
        # Verifica se o comando foi executado com sucesso
        if resultado.returncode != 0:
            logger.error(f"Erro ao extrair URL: {resultado.stderr}")
            return None
        
        # Extrai a URL do stream
        stream_url = resultado.stdout.strip()
        
        # Verifica se a URL do stream foi extraída com sucesso
        if not stream_url:
            logger.warning("yt-dlp não retornou nenhuma URL")
            return None
        
        logger.info(f"[OK] URL do stream extraída com sucesso!")
        return stream_url 

    # Tratamento de erros
    except subprocess.TimeoutExpired:
        logger.error("Timeout ao tentar extrair URL")
        return None
    except Exception as e:
        logger.error(f"Erro ao extrair URL: {e}")
        return None

# --------------------------------------------------------------------------------------------------------------------------------------

def _construir_comando_ffmpeg(stream_url: str, output_pattern: str, segment_duration: int = 30, max_duration: int = 300) -> List[str]:
    """
    Constrói o comando FFmpeg para captura e segmentação de stream.
    
    Args:
        stream_url(str): URL do stream de entrada
        output_pattern(str): Padrão de nome para os arquivos de saída (ex: segment_%03d.mp4)
        segment_duration(int): Duração de cada segmento em segundos
        max_duration(int): Duração máxima da captura em segundos
        
    Returns:
        List[str]: Lista com o comando FFmpeg completo
    """
    comando = [
        "ffmpeg",
        "-y",                                    # Sobrescreve arquivos sem perguntar
        "-i", stream_url,                        # URL do stream de entrada
        "-t", str(max_duration),                 # Duração máxima da captura
        "-f", "segment",                         # Formato de saída: segmentação
        "-segment_time", str(segment_duration),  # Duração de cada segmento
        "-reset_timestamps", "1",                # Reseta timestamps para cada segmento
        "-c", "copy",                            # Copia streams sem re-encoding (rápido)
        "-avoid_negative_ts", "make_zero",       # Evita timestamps negativos
        output_pattern                           # Padrão de saída
    ]
    
    return comando

# --------------------------------------------------------------------------------------------------------------------------------------

def executar_agente_coletor(stream_url: str, output_dir: str = "backend/data/stream_segments", segment_duration: int = 30, max_duration: int = 300) -> Optional[Dict[str, Any]]:
    """
    Agente Coletor de Streams: captura e segmenta streams ao vivo usando FFmpeg.
    
    Recebe uma URL de stream (HLS, YouTube Live, RTMP, etc.) e gera segmentos de vídeo
    em intervalos regulares, prontos para processamento pelos outros agentes.
    
    Suporta:
    - Streams HLS (.m3u8)
    - YouTube Lives, Twitch, etc (extrai URL do stream automaticamente via yt-dlp)
    - RTMP/RTSP streams
    
    Args:
        stream_url(str): URL do stream a ser capturado (ex: Twitch, YouTube, etc.)
        output_dir(str): Diretório onde os segmentos serão salvos
        segment_duration(int): Duração de cada segmento em segundos (padrão: 30s)
        max_duration(int): Duração máxima da captura em segundos (padrão: 300s = 5min)
        
    Returns:
        Optional[Dict[str, Any]]: Dicionário com status e informações dos segmentos, ou None em caso de falha
    """
    
    logger.info(f"-> [Agente Coletor] Iniciando captura de stream: {stream_url}")
    
    # Valida a URL do stream
    if not _validar_url_stream(stream_url):
        logger.error(f"Erro: URL de stream inválida: {stream_url}")
        return None
    
    # Verifica se a URL do stream é direta
    is_direct_stream = stream_url.endswith(('.m3u8', '.mp4', '.mkv', '.ts')) or stream_url.startswith(('rtmp://', 'rtsp://')) or os.path.exists(stream_url)
    
    # Se a URL do stream não for direta, tenta extrair a URL real
    if not is_direct_stream:
        logger.info("URL requer extração (YouTube/Twitch/etc)")
        stream_url_real = _extrair_url_stream(stream_url)
        
        if stream_url_real:
            logger.info(f"Usando URL do stream extraída")
            stream_url = stream_url_real
        else:
            logger.warning("Aviso: Falha na extração, tentando usar URL original...")
    
    # Cria o diretório de saída se não existir
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Diretório de saída: {output_dir}")
    except Exception as e:
        logger.error(f"Erro ao criar diretório de saída {output_dir}: {e}")
        return None
    
    # Define o padrão de nome dos segmentos
    output_pattern = os.path.join(output_dir, "segment_%03d.mp4")
    
    # Constrói o comando FFmpeg
    comando = _construir_comando_ffmpeg(
        stream_url=stream_url,               
        output_pattern=output_pattern,         
        segment_duration=segment_duration,    
        max_duration=max_duration              
    )
    
    # Exibe o comando que será executado
    logger.info(f"Executando FFmpeg: {' '.join(comando)}")
    logger.info(f"Capturando por até {max_duration}s em segmentos de {segment_duration}s...")
    
    try:
        # Executa o comando FFmpeg
        inicio = time.time()
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True
        )

        # Calcula a duração total da captura
        duracao_total = time.time() - inicio
    
        # Verifica se o FFmpeg executou com sucesso
        if resultado.returncode != 0:
            logger.error(f"Saída de erro do FFmpeg: {resultado.stderr}")
            raise RuntimeError("Erro ao capturar stream com FFmpeg.")
        
        # Lista os segmentos gerados
        segmentos = sorted([
            os.path.join(output_dir, f) # 
            for f in os.listdir(output_dir) 
            if f.startswith("segment_") and f.endswith(".mp4")
        ])
        
        # Verifica se os segmentos foram gerados
        if not segmentos:
            logger.warning("Aviso: Nenhum segmento foi gerado.")
            return None
        
        logger.info(f"[OK] Captura concluída em {duracao_total:.2f}s!")
        if resultado.returncode != 0:
            logger.error(f"Saída de erro do FFmpeg: {resultado.stderr}")
            raise RuntimeError("Erro ao capturar stream com FFmpeg.")
        
        # Lista os segmentos gerados
        segmentos = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("segment_") and f.endswith(".mp4")])
        
        if not segmentos:
            logger.warning("Aviso: Nenhum segmento foi gerado.")
            return None
        
        logger.info(f"[OK] Captura concluída em {duracao_total:.2f}s!")
        logger.info(f"Total de segmentos gerados: {len(segmentos)}")
        
        # Retorna informações sobre a captura
        return {
            "status": "sucesso",
            "output_dir": output_dir,
            "segment_count": len(segmentos),
            "segment_paths": segmentos,
            "segment_duration": segment_duration,
            "total_duration": duracao_total
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Erro: Timeout na captura do stream.")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado durante a captura: {str(e)}")
        return None
