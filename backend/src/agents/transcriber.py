import os # Interage com o Sistema Operacional
import subprocess # Executa outros programas/comandos do SO
import whisper # Biblioteca da OpenAI para transcrição de áudio
import json # Usada para salvar o dicionário da transcrição em formato JSON
from dotenv import load_dotenv # Acessa as variáveis de ambiente 
from pathlib import Path # Usada para lidar com caminhos de arquivos 
import logging # Usada para logging

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log = logging.getLogger("transcriber")

# --------------------------------------------------------------------------------------------------------------------------------------

def download_youtube_video(url: str, output_path: str) -> bool:
    """
    Baixa o vídeo do Youtube utilizando yt-dlp e salva em output_path (formato mp4).

    Args: 
        url(str): URL do Youtube
        output_path(str): Caminho onde o vídeo será salvo

    Returns: 
        bool: True se o download foi bem sucedido, False caso contrário
    """
    try:
        log.info(f"Iniciando download do vídeo: {url}")
        
        # Garante que o diretório de saída existe
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Executa o comando yt-dlp para baixar o vídeo
        # Usa opções robustas para contornar bloqueios do YouTube
        command = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",  # Formato preferencial
            "-o", output_path,
            "--no-playlist",  # Apenas o vídeo, não a playlist
            "--extractor-args", "youtube:player_client=android",  # Usa cliente Android (mais estável)
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--referer", "https://www.youtube.com/",
            "--retries", "10",  # Mais tentativas
            "--fragment-retries", "10",  # Retry de fragmentos
            "--ignore-errors",  # Continua mesmo com erros menores
            url
        ]

        log.info(f"Executando: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600  # Timeout de 10 minutos
        )

        # Verifica se o retorno é diferente de 0, que indica erro
        if result.returncode != 0:
            log.error(f"Erro ao baixar vídeo: {result.stderr}")
            log.error(f"Stdout: {result.stdout}")
            return False

        # Verifica se o arquivo foi criado
        if not os.path.exists(output_path):
            log.error(f"Arquivo não foi criado em: {output_path}")
            return False

        # Verifica o tamanho do arquivo baixado
        file_size = os.path.getsize(output_path)
        log.info(f"Download concluído! Arquivo: {output_path} ({file_size / 1024 / 1024:.2f} MB)")

        # Caso o download seja bem sucedido, retorna True
        return True

    except subprocess.TimeoutExpired:
        log.error(f"Timeout ao baixar vídeo: {url}")
        return False
    except Exception as e:
        log.exception(f"Erro inesperado ao baixar vídeo: {e}")
        return False

# --------------------------------------------------------------------------------------------------------------------------------------

def transcricao_whisper(video_path: str, model_size: str = "base") -> dict | None:
    """
    Transcreve o áudio de um arquivo de vídeo usando o modelo Whisper.

    Args: 
        video_path(str): Caminho para o arquivo de vídeo
        model_size(str): Tamanho do modelo do Whisper ("tiny", "base", "small", "medium", "large")

    Returns: 
        dict | None: Resultados da transcrição contendo texto, segmentos, etc., ou None em caso de erro
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(video_path):
            log.error(f"Arquivo de vídeo não encontrado: {video_path}")
            return None

        # Carrega o modelo Whisper com o tamanho passado como parâmetro
        log.info(f"Carregando modelo Whisper: {model_size}")
        modelo = whisper.load_model(model_size)
        log.info(f"Modelo {model_size} carregado com sucesso")

        # Realiza a transcrição do áudio do vídeo
        log.info(f"Iniciando transcrição do vídeo: {video_path}")
        result = modelo.transcribe(
            video_path,
            fp16=False,  
            temperature=0,
            condition_on_previous_text=False,
            verbose=True  # Mostra o progresso da transcrição
        )

        # Verifica se a transcrição foi concluída com sucesso
        if result and "text" in result:
            text_length = len(result["text"]) # Quantidade de caracteres do texto transcrito
            segments_count = len(result.get("segments", [])) # Quantidade de segmentos
            log.info(f"Transcrição concluída! Texto: {text_length} caracteres, Segmentos: {segments_count}")

            # Retorna o resultado da transcrição, em um dicionário incluindo texto, segmentos e idioma
            return result
        else:
            log.error("Transcrição retornou resultado vazio ou inválido")
            # Retorna None se a transcrição falhar 
            return None

    except Exception as e:
        log.exception(f"Erro durante a transcrição: {e}")
        # Retorna None se ocorrer qualquer tipo de erro durante a transcrição
        return None

# --------------------------------------------------------------------------------------------------------------------------------------

def transcricao_youtube_video(url: str, temp_video_path: str = "data/temp/temp_video.mp4", model_size: str = "base", output_json_path: str | None = None) -> dict | None:
    """
    Executa o processo completo: Baixa o vídeo, faz a transcrição e salva o resultado.

    Args: 
        url(str): URL do vídeo no Youtube
        temp_video_path(str): Caminho para salvar o vídeo baixado temporariamente
        model_size(str): Tamanho do modelo Whisper a ser usado
        output_json_path(str | None): Caminho para salvar a transcrição final em JSON

    Returns: 
        dict | None: Dicionário com o resultado da transcrição ou None em caso de erro
    """
    try:
        log.info(f"Iniciando pipeline de transcrição para: {url}")
        log.info(f"Modelo: {model_size}, Vídeo temporário: {temp_video_path}")

        # Garante que o diretório para o vídeo temporário exista (cria se não existir)
        temp_dir = os.path.dirname(temp_video_path)
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)

        # Baixar o vídeo do Youtube usando yt-dlp
        log.info("Etapa 1/3: Baixando vídeo do YouTube...")
        if not download_youtube_video(url, temp_video_path):
            log.error("Falha no download do vídeo!")
            return None

        # Transcrever o áudio baixado com o Whisper
        log.info("Etapa 2/3: Transcrevendo áudio com Whisper...")
        transcript = transcricao_whisper(temp_video_path, model_size)
        
        # Caso a transcrição falhe por qualquer motivo
        if not transcript:
            log.error("Falha na transcrição!")
            return None

        # Salvar o resultado em JSON se um caminho foi fornecido
        if output_json_path:
            log.info("Etapa 3/3: Salvando transcrição em JSON...")
            try:
                # Garante que o diretório de saída exista
                output_dir = os.path.dirname(output_json_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

                # Salva o dicionário completo em formato JSON
                with open(output_json_path, "w", encoding="utf-8") as jf:
                    json.dump(transcript, jf, ensure_ascii=False, indent=4)

                # Mensagem de sucesso
                log.info(f"Transcrição salva em: {output_json_path}")
            except Exception as e:

                # Caso ocorra algum erro ao salvar os arquivos
                log.exception(f"Erro ao salvar JSON: {e}")
                # Continua mesmo se falhar ao salvar, retorna o resultado

        log.info("Pipeline de transcrição concluído com sucesso!")
        # Retorna o resultado da transcrição
        return transcript

    except Exception as e:
        log.exception(f"Erro inesperado no pipeline de transcrição: {e}")
        return None

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Exemplo de uso - teste interativo do módulo
    youtube_url = input("Cole a URL do vídeo do YouTube: ")
    output_json_path = "data/temp/transcricao_final.json"

    # Executa o pipeline completo de transcrição
    transcript = transcricao_youtube_video(
        youtube_url,
        model_size="base",
        output_json_path=output_json_path
    )

    if transcript:
        print("\nTranscrição concluída!")
        print(f"Texto: {transcript['text'][:200]}...")  # Primeiros 200 caracteres
    else:
        print("Falha na transcrição.")
