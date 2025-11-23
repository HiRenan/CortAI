import os # Interage com o Sistema Operacional
import json # Usada para salvar o dicionário da transcrição em formato JSON
from typing import Dict, Any, Optional # Usada para tipar as funções
import whisper # Biblioteca OpenAI Whisper
import torch # PyTorch para verificação de GPU

# Variável global para armazenar o modelo carregado (Singleton)
_whisper_model = None

def get_model():
    """
    Carrega o modelo Whisper de forma preguiçosa (Lazy Loading).
    """
    global _whisper_model
    if _whisper_model is None:
        print("Carregando modelo Whisper (base)... isso pode demorar um pouco.")
        # Usa GPU se disponível, senão CPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Usando dispositivo: {device}")
        _whisper_model = whisper.load_model("base", device=device)
    return _whisper_model

# --------------------------------------------------------------------------------------------------------------------------------------

def executar_transcricao_segmento(segment_path: str) -> Optional[Dict[str, Any]]:
    """
    Agente Transcritor adaptado para processar um único segmento de áudio/vídeo usando Whisper.
    
    Recebe o caminho de um segmento (chunk) e retorna a transcrição e os metadados.

    Args:
        segment_path (str): Caminho absoluto ou relativo para o arquivo de segmento (ex: segmento000.mp4).

    Returns:
        Optional[Dict[str, Any]]: Um dicionário com a transcrição e metadados, ou None em caso de falha.
    """

    print(f"\n-> [Agente Transcritor Stream] Processando segmento: {segment_path}")
    
    # Verifica se o arquivo de segmento existe
    if not os.path.exists(segment_path):
        print(f"Erro: Arquivo de segmento não encontrado em {segment_path}")
        return None

    try:
        # Carrega o modelo
        model = get_model()
        
        # Realiza a transcrição
        # fp16=False é importante para CPU, mas se tiver GPU pode ser True. 
        # Vamos manter False por segurança ou verificar device.
        device = "cuda" if torch.cuda.is_available() else "cpu"
        use_fp16 = (device == "cuda")
        
        result = model.transcribe(segment_path, fp16=use_fp16) 
        text = result["text"].strip()
        
        # Extrai o nome do segmento para calcular timestamps relativos (se necessário)
        segment_name = os.path.basename(segment_path)
        
        # Cria um dicionário com a transcrição e metadados
        transcricao_result = {
            "text": text,
            "segment_file": segment_name,
            # Mantemos compatibilidade com o formato esperado pelo analista
            # O Whisper retorna segmentos detalhados em result['segments'] se precisarmos
        }
        
        print(f"Texto transcrito ({len(text)} chars): {text[:100]}...") 
        
        # Salva a transcrição em um arquivo JSON temporário para persistência
        output_json_path = segment_path.replace(".mp4", ".json")
        
        # Salva o dicionário em um arquivo JSON
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(transcricao_result, f, indent=4, ensure_ascii=False)
            
        print(f"Transcrição concluída e salva em: {output_json_path}")
        
        # Retorna um dicionário com o status e as informações da transcrição
        return {
            "status": "sucesso",
            "transcription_path": output_json_path,
            "transcription_data": transcricao_result
        }

    except Exception as e:
        # Retorna um dicionário com o status e a mensagem de erro
        print(f"Erro inesperado durante a transcrição do segmento {segment_path}: {str(e)}")
        return None

# --------------------------------------------------------------------------------------------------------------------------------------

def transcricao_youtube_video(url: str, temp_video_path: str, model_size: str = "base", output_json_path: str = None) -> Optional[Dict[str, Any]]:
    """
    Baixa um vídeo do YouTube e realiza a transcrição usando Whisper.
    Esta função é usada pelo transcriber_worker.py para processar vídeos completos do YouTube.
    
    Args:
        url (str): URL do vídeo do YouTube
        temp_video_path (str): Caminho onde o vídeo será salvo temporariamente
        model_size (str): Tamanho do modelo Whisper (tiny, base, small, medium, large)
        output_json_path (str): Caminho onde a transcrição será salva em JSON
        
    Returns:
        Optional[Dict[str, Any]]: Dicionário com a transcrição e metadados, ou None em caso de falha
    """
    
    print(f"\n-> [Agente Transcritor YouTube] Processando vídeo: {url}")
    
    try:
        # Importa yt-dlp para download do vídeo
        import yt_dlp
        
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
        
        # Configurações do yt-dlp
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Baixa vídeo + áudio
            'outtmpl': temp_video_path,
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',  # Garante que o output seja MP4
        }
        
        # Baixa o vídeo
        print(f"Baixando vídeo do YouTube...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        print(f"Vídeo baixado em: {temp_video_path}")
        
        # Verifica se o arquivo foi baixado
        if not os.path.exists(temp_video_path):
            print(f"Erro: Arquivo de vídeo não foi criado em {temp_video_path}")
            return None
        
        # Carrega o modelo Whisper
        print(f"Carregando modelo Whisper ({model_size})...")
        model = get_model()
        
        # Realiza a transcrição
        device = "cuda" if torch.cuda.is_available() else "cpu"
        use_fp16 = (device == "cuda")
        
        print(f"Transcrevendo vídeo...")
        result = model.transcribe(temp_video_path, fp16=use_fp16)
        text = result["text"].strip()
        
        # Cria o dicionário de resultado
        transcricao_result = {
            "text": text,
            "url": url,
            "video_path": temp_video_path,
            "segments": result.get("segments", [])  # Inclui segmentos detalhados do Whisper
        }
        
        print(f"Texto transcrito ({len(text)} chars): {text[:100]}...")
        
        # Salva em JSON se o caminho foi fornecido
        if output_json_path:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(transcricao_result, f, indent=4, ensure_ascii=False)
            print(f"Transcrição salva em: {output_json_path}")
        
        return transcricao_result
        
    except Exception as e:
        print(f"Erro durante download/transcrição do YouTube: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

