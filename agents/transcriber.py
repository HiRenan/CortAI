import os # Interage com o Sistema Operacional
import subprocess # Executa outros programas/comandos do SO
import whisper # Biblioteca da OpenAI para transcrição de áudio
import json # Usada para salvar o dicionário da transcrição em formato JSON
from dotenv import load_dotenv # Acessa as variáveis de ambiente 

load_dotenv()
ffmpeg_path = os.getenv("FFMPEG_PATH")

# --------------------------------------------------------------------------------------------------------------------------------------

def download_youtube_video(url, output_path): 
    """
    Baixa o vídeo do Youtube utilizando yt-dlp e salva em output_path (formato mp4).

    Args: 
        url(str) - URL do Youtube
        output_path(str) - Caminho onde o vídeo será salvo

    Returns: 
        bool - True se o download foi bem sucedido, e False caso contrário
    """

    # Executa o comando yt-dlp para baixar o vídeo em formato mp4
    result = subprocess.run(
        ["yt-dlp", "-f", "mp4", "-o", output_path, url], # Comando e argumentos 
        capture_output=True, # Captura a saída 
        text=True # Interpreta a saída como texto 
    )

    # Verifica se o retorno é diferente de 0, que indica erro
    if result.returncode != 0: 
        print(f"Erro ao baixar vídeo: {result.stderr}")
        return False 
    
    # Caso o download seja bem sucedido, retorna True
    return True 

# --------------------------------------------------------------------------------------------------------------------------------------

def trancricao_whisper(video_path, model_size="base"): 
    """
    Transcreve o áudio de um arquivo de vídeo usando o modelo Whisper.

    Args: 
        vídeo_path(str) - Caminho para o arquivo de vídeo
        model_size(str) - Tamanho do modelo do Whisper ("tiny", "base", "small", "medium", "large")

    Returns: 
        dict: Resultados da transcrição contendo texto, segmentos, começo, duração, etc.
    """

    # Carrega o modelo Whisper com o tamanho passado como parâmetro
    modelo = whisper.load_model(model_size)

    # Realiza a transcrição do áudio do vídeo 
    result = modelo.transcribe(video_path, fp16=False)

    # Retorna o resultado da transcrição, em um dicionário incluindo texto, segmentos e idioma 
    return result 

# --------------------------------------------------------------------------------------------------------------------------------------

def transcricao_youtube_video(url, temp_video_path="data/temp_video.mp4", model_size="base", output_json_path: str = None): 
    """
    Executa o processo completo: Baixa o vídeo, faz a transcrição e salva o resultado. 

    Args: 
        url(str) - URL do vídeo no Youtube
        temp_video_path(str) - Caminho para salvar o vídeo baixado temporariamente 
        model_size(str) - Tamanho do modelo Whisper a ser usado
        output_file_path(str) - Caminho para salvar a transcrição final (.txt)

    Returns: 
        dict/None - Dicionário com o resutado da transcrição ou None em caso de erro. 
    """

    # Garante que o diretório para o vídeo temporário exista (cria se não existir)
    temp_dir = os.path.dirname(temp_video_path)
    if temp_dir and not os.path.exists(temp_dir): 
        os.makedirs(temp_dir) 

    # Baixar o vídeo do Youtube usando yt-dlp
    if not download_youtube_video(url, temp_video_path): 
        print("Falha no download!")
        return None 

    # Transcrever o áudio baixado com o Whisper
    transcript = trancricao_whisper(temp_video_path, model_size)

    # Caso a transcrição tenha sido feita e um caminho de saída tenha sido fornecido
    if transcript and output_json_path: 
        try: 
            # Garante que o diretório de saída exista 
            output_dir = os.path.dirname(output_json_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Salva o dicionário completo em formato JSON
            with open(output_json_path, "w", encoding="utf-8") as jf:
                json.dump(transcript, jf, ensure_ascii=False, indent=4, sort_keys=True)

            # Mensagens de sucesso
            print(f"Dicionário completo salvo em: {output_json_path}")
        except Exception as e: 
            # Caso ocorra algum erro ao salvar os arquivos 
            print(f"Erro ao salvar transcrição JSON: {e}")
            return None
    elif not transcript: 
        # Caso a transcrição falhe por qualquer motivo
        print("A transcrição falhou, nada para salvar")
        return None

    # Retorna o dicionário da transcrição completo
    return transcript

# --------------------------------------------------------------------------------------------------------------------------------------
    
if __name__ == "__main__":
    # Exemplo de uso - teste interativo do módulo
    youtube_url = input("Cole a URL do vídeo do YouTube: ")

    output_json_path = "data/transcricao_final.json"
    
    # Executa o pipeline completo de transcrição
    transcript = transcricao_youtube_video(
            youtube_url,
            model_size="base",
            output_json_path=output_json_path
        )
    
    if transcript:
        print("Transcrição concluída!\n")
        print(transcript) 
    else:
        print("Falha na transcrição.")
        