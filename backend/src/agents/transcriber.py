import os # Interage com o Sistema Operacional
import json # Usada para salvar o dicionário da transcrição em formato JSON
from typing import Dict, Any, Optional # Usada para tipar as funções
from faster_whisper import WhisperModel  # faster-whisper (4-5x mais rápido)

# Variável global para armazenar o modelo carregado (Singleton)
_whisper_model = None

def get_model():
    """
    Carrega o modelo Whisper de forma preguiçosa (Lazy Loading).
    Usa faster-whisper para performance 4-5x melhor em CPU.
    """
    global _whisper_model
    if _whisper_model is None:
        print("Carregando modelo faster-whisper (base)... isso pode demorar um pouco.")
        # faster-whisper usa device="cpu" ou "cuda"
        # compute_type: "int8" para CPU (mais rápido), "float16" para GPU
        device = "cpu"  # AMD GPU (ROCm) não é suportado diretamente, usando CPU otimizado
        compute_type = "int8"  # Quantização para CPU (4x mais rápido com pouca perda)

        print(f"Usando dispositivo: {device} com compute_type: {compute_type}")
        print("ℹ️ faster-whisper é 4-5x mais rápido que openai-whisper em CPU!")

        # Cria modelo com otimizações
        _whisper_model = WhisperModel(
            "base",  # Modelo base (boa qualidade/velocidade)
            device=device,
            compute_type=compute_type,
            num_workers=4,  # Usa 4 threads para CPU
            cpu_threads=8   # Threads para processamento
        )
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

        # Realiza a transcrição com faster-whisper
        # faster-whisper retorna (segments, info) em vez de dict
        segments, info = model.transcribe(
            segment_path,
            beam_size=5,
            vad_filter=True,  # Voice Activity Detection (remove silêncio)
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Converte segments para lista e extrai texto
        segments_list = list(segments)
        text = " ".join([seg.text for seg in segments_list]).strip()
        
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
        print(f"Carregando modelo faster-whisper ({model_size})...")
        model = get_model()

        # Realiza a transcrição com faster-whisper
        print(f"Transcrevendo vídeo com faster-whisper... (4-5x mais rápido!)")
        segments, info = model.transcribe(
            temp_video_path,
            beam_size=5,
            vad_filter=True,  # Remove silêncios automaticamente
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Converte generator para lista e extrai dados
        segments_list = []
        full_text = []

        for segment in segments:
            full_text.append(segment.text)
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })

        text = " ".join(full_text).strip()

        # Cria o dicionário de resultado (compatível com formato antigo)
        transcricao_result = {
            "text": text,
            "url": url,
            "video_path": temp_video_path,
            "segments": segments_list,  # Segmentos detalhados (compatível)
            "language": info.language,
            "duration": info.duration
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

# --------------------------------------------------------------------------------------------------------------------------------------

def transcrever_video_local(video_path: str, output_json_path: str, model_size: str = "base") -> Optional[Dict[str, Any]]:
    """
    Transcreve um arquivo de vídeo local com Whisper (sem download).

    Args:
        video_path (str): Caminho do arquivo de vídeo já disponível localmente
        output_json_path (str): Caminho onde a transcrição será salva
        model_size (str): Tamanho do modelo Whisper
    """

    if not os.path.exists(video_path):
        print(f"Erro: Arquivo de vídeo não encontrado: {video_path}")
        return None

    try:
        # Carrega o modelo Whisper
        print(f"Carregando modelo faster-whisper ({model_size})...")
        model = get_model()

        print(f"Transcrevendo vídeo local com faster-whisper... (4-5x mais rápido!)")
        segments, info = model.transcribe(
            video_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # Converte segments para formato compatível
        segments_list = []
        full_text = []

        for segment in segments:
            full_text.append(segment.text)
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })

        text = " ".join(full_text).strip()

        transcricao_result = {
            "text": text,
            "video_path": video_path,
            "segments": segments_list,
            "language": info.language,
            "duration": info.duration
        }

        # Salva o dicionário em um arquivo JSON
        output_dir = os.path.dirname(output_json_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(transcricao_result, f, indent=4, ensure_ascii=False)

        print(f"Transcrição concluída e salva em: {output_json_path}")
        return transcricao_result

    except Exception as e:
        print(f"Erro inesperado durante a transcrição local: {str(e)}")
        return None

