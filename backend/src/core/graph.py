# Importa os agentes especializados para cada etapa do processo
# CORRIGIDO: Imports relativos para funcionar dentro do pacote backend
import json
import subprocess
from typing import TypedDict, Optional, Dict, Any
from pathlib import Path
import os

from src.agents.transcriber import transcricao_youtube_video, transcrever_video_local
from src.agents.analyst import AnalystAgent  # Novo agente com JSON/Pydantic
from src.agents.editor import executar_agente_editor, _normalize_highlights
from src.agents.collector_streams import executar_agente_coletor
from src.agents.screenwriter import make_srt, make_vtt, choose_thumbnail

# Importa progress tracking
from src.core.progress import update_progress

# Importa configurações centralizadas
from src.core.config import DATA_DIR

# Importa funções de chunking
from src.utils.chunking import should_use_chunking

# Importa a estrutura principal do grafo (StateGraph) e o marcador de fim de fluxo (END)
from langgraph.graph import StateGraph, END

# Importa tipos para tipagem estática
STREAM_PREFIXES = ("rtmp://", "rtsp://")
STREAM_SUFFIXES = (".m3u8",)


def should_collect_stream(url: str) -> bool:
    lu = url.lower()
    if lu.startswith(STREAM_PREFIXES):
        return True
    if lu.endswith(STREAM_SUFFIXES):
        return True
    if "live" in lu and ("youtube.com/" in lu or "twitch.tv" in lu or "facebook.com" in lu):
        return True
    return False


def concat_segments_ffmpeg(segment_paths: list[str], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    list_file = output_path + ".concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            f.write(f"file '{p}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Saída ffmpeg concat:", result.stderr)
        raise RuntimeError("Erro ao concatenar segmentos")
    return output_path


def first_highlight_range(highlight_json_path: str) -> Optional[Dict[str, float]]:
    try:
        with open(highlight_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        highlights = _normalize_highlights(data)
        if not highlights:
            return None
        h = highlights[0]
        return {"start": float(h.get("start", h.get("inicio", 0))), "end": float(h.get("end", h.get("fim", 0)))}
    except Exception as e:
        print(f"[warn] Não foi possível ler highlights: {e}")
        return None


def build_clipped_transcription(transcription_path: str, start: float, end: float) -> Dict[str, Any]:
    with open(transcription_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data.get("segments", [])
    clipped = []
    for seg in segments:
        seg_start = float(seg.get("start", 0))
        seg_end = float(seg.get("end", seg_start))
        if seg_end < start or seg_start > end:
            continue
        new_start = max(seg_start, start) - start
        new_end = min(seg_end, end) - start
        clipped.append({
            "start": new_start,
            "end": new_end if new_end > new_start else new_start + 0.5,
            "text": str(seg.get("text", "")).strip()
        })
    return {"segments": clipped}


# ----------------------------------------------------------------------
# Helper function to generate unique paths per video
# ----------------------------------------------------------------------

def get_video_paths(video_id: int) -> Dict[str, str]:
    """
    Generates unique file paths for a video based on its ID.

    This prevents file collisions when multiple videos are being processed.

    Args:
        video_id: The database ID of the video

    Returns:
        Dictionary with all required file paths for this video
    """
    # Create video-specific directory
    video_dir = Path(DATA_DIR) / f"video_{video_id}"
    video_dir.mkdir(parents=True, exist_ok=True)

    # Create clips directory for this video
    clips_dir = video_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    return {
        "video_path": str(video_dir / "temp_video.mp4"),
        "transcription_path": str(video_dir / "transcription.json"),
        "highlight_json_path": str(video_dir / "highlights.json"),
        "clips_dir": str(clips_dir),
        "segments_dir": str(video_dir / "segments"),
        "log_dir": str(video_dir / "logs"),
    }


def cleanup_video_files(video_id: int):
    """
    Cleans up temporary files for a video after processing.

    Args:
        video_id: The database ID of the video
    """
    try:
        video_dir = Path(DATA_DIR) / f"video_{video_id}"
        if video_dir.exists():
            # Remove the temporary video file (largest file)
            temp_video = video_dir / "temp_video.mp4"
            if temp_video.exists():
                temp_video.unlink()
                print(f"Arquivo temporário removido: {temp_video}")

            # Keep transcription and highlights JSON for debugging
            # Keep clips directory with generated clips

    except Exception as e:
        print(f"Aviso: Erro ao limpar arquivos temporários do vídeo {video_id}: {e}") 

# ----------------------------------------------------------------------
# Define a classe (dicionário) que representa o estado do grafo
# total = False, indica que não é necessário preencher todos os campos de uma vez só
class CortAIState(TypedDict, total=False):
    url: str
    video_path: str
    transcription: Dict[str, Any]
    transcription_path: str
    highlight: Dict[str, Any]
    highlight_path: str
    error: str

    # Progress tracking fields
    video_id: Optional[int]
    celery_task: Optional[Any]  # Celery task instance for state updates

    # Configuration fields
    max_highlights: Optional[int]  # Maximum number of highlights to generate (default: 5)
    include_subtitles: Optional[bool]  # Include burned-in subtitles in clips (default: True)
    subtitle_style: Optional[str]  # Subtitle style: 'youtube' (default)


# Nó 1: Transcrever vídeo
def node_transcrever(state: CortAIState) -> CortAIState:
    """
    Primeiro nó: responsável por baixar o vídeo e gerar a transcrição (Whisper)
    """
    print("\n -> [1/3] Transcrevendo vídeo...\n")

    video_id = state.get("video_id")
    celery_task = state.get("celery_task")
    url = state["url"]

    # Generate unique paths for this video
    if not video_id:
        state["error"] = "video_id não fornecido no state!"
        return state

    paths = get_video_paths(video_id)
    print(f"  Usando paths únicos para vídeo {video_id}:")
    print(f"    - Video: {paths['video_path']}")
    print(f"    - Transcrição: {paths['transcription_path']}")

    # Progress: 5% - Baixando vídeo
    if video_id:
        update_progress(video_id, "transcribing", 5, "Baixando vídeo...")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'transcribing', 'percentage': 5, 'message': 'Baixando vídeo...'}
        )

    # Progress: 20% - Transcrevendo áudio
    if video_id:
        update_progress(video_id, "transcribing", 20, "Transcrevendo áudio...")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'transcribing', 'percentage': 20, 'message': 'Transcrevendo áudio...'}
        )

    # Decide se usa coletor de stream antes da transcrição
    use_collector = should_collect_stream(url) or state.get("use_stream_collector", False)

    if use_collector:
        print("  URL parece stream. Coletando segmentos antes de transcrever...")
        collect_result = executar_agente_coletor(
            stream_url=url,
            output_dir=paths["segments_dir"],
            segment_duration=60,
            max_duration=300
        )
        if not collect_result or not collect_result.get("segment_paths"):
            state["error"] = "Falha na coleta do stream."
            return state

        try:
            merged_video = concat_segments_ffmpeg(collect_result["segment_paths"], paths["video_path"])
        except Exception as e:
            state["error"] = f"Erro ao concatenar segmentos: {e}"
            return state

        transcription = transcrever_video_local(
            video_path=merged_video,
            output_json_path=paths["transcription_path"]
        )
    else:
        transcription = transcricao_youtube_video(
            url=url,
            temp_video_path=paths["video_path"],
            output_json_path=paths["transcription_path"]
        )

    state["video_path"] = paths["video_path"]
    state["transcription_path"] = paths["transcription_path"]
    state["transcription"] = transcription

    # Progress: 33% - Transcrição concluída
    if video_id:
        update_progress(video_id, "transcribing", 33, "Transcrição concluída")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'transcribing', 'percentage': 33, 'message': 'Transcrição concluída'}
        )

    print("\n ✔ Transcrição concluída!")
    return state

# Nó 2: Analisar transcrição com AnalystAgent
# ----------------------------------------------------------------------

def node_analisar(state: CortAIState) -> CortAIState:
    """
    Segundo nó: o 'cérebro'. Lê a transcrição e decide o que é importante.

    Usa chunking automático para transcrições longas (>20.000 caracteres).
    """
    print("\n -> [2/3] Analisando transcrição...")

    video_id = state.get("video_id")
    celery_task = state.get("celery_task")
    max_highlights = state.get("max_highlights", 5)  # Padrão: 5 highlights

    # Progress: 40% - Analisando transcrição
    if video_id:
        update_progress(video_id, "analyzing", 40, "Analisando transcrição...")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'analyzing', 'percentage': 40, 'message': 'Analisando transcrição...'}
        )

    transcription_path = state.get("transcription_path")
    if not transcription_path:
        state["error"] = "Transcription path não encontrado no estado!"
        return state

    # Carrega a transcrição completa do arquivo
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription_json = json.load(f)
    except Exception as e:
        state["error"] = f"Falha ao carregar transcrição: {str(e)}"
        if video_id:
            update_progress(video_id, "analyzing", 0, f"Erro leitura transcrição: {e}")
        return state

    texto_transcricao = transcription_json.get("text", "").strip()
    segments = transcription_json.get("segments", [])

    if not texto_transcricao:
        state["error"] = "Transcrição vazia ou inválida!"
        return state

    # Cria o agente analista
    agent = AnalystAgent()

    print(f"  Transcrição ({len(texto_transcricao)} chars)")
    print(f"  Usando processamento direto")

    # Usa método normal (passando caminho do arquivo)
    try:
        highlight_result = agent.run(transcription_path)
    except Exception as e:
        state["error"] = f"AnalystError: {e}"
        return state

    # Normaliza saída para formato esperado pelo editor
    highlights = []
    if isinstance(highlight_result, dict):
        if "highlights" in highlight_result and isinstance(highlight_result["highlights"], list):
            highlights = highlight_result["highlights"]
        else:
            try:
                start = float(highlight_result.get("highlight_inicio_segundos", highlight_result.get("start", 0)))
                end = float(highlight_result.get("highlight_fim_segundos", highlight_result.get("end", 0)))
                summary = highlight_result.get("resposta_bruta") or highlight_result.get("summary") or ""
                score = highlight_result.get("score", 0)
                highlights = [{"start": start, "end": end, "summary": summary, "score": score}]
            except Exception:
                highlights = []

    state["highlight"] = {"highlights": highlights}

    # Log dos highlights encontrados
    num_highlights = len(highlights)
    print(f"\n  Encontrados {num_highlights} highlights:")
    for idx, h in enumerate(highlights, 1):
        print(f"    {idx}. {float(h.get('start', 0)):.1f}s - {float(h.get('end', 0)):.1f}s")

    # Salva JSON para o editor usando path único
    paths = get_video_paths(video_id)
    highlight_json_path = paths["highlight_json_path"]

    try:
        with open(highlight_json_path, "w", encoding="utf-8") as f:
            json.dump(state["highlight"], f, indent=4, ensure_ascii=False)
        print(f"\n  Arquivo de corte salvo em: {highlight_json_path}")

        # Store path in state for next node
        state["highlight_json_path"] = highlight_json_path
    except Exception as e:
        state["error"] = f"Erro ao salvar highlight JSON: {str(e)}"
        return state

    # Progress: 66% - Análise concluída
    if video_id:
        update_progress(video_id, "analyzing", 66, f"Análise concluída - {num_highlights} highlights encontrados")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'analyzing', 'percentage': 66, 'message': f'Análise concluída - {num_highlights} highlights'}
        )

    print("\n ✔ Análise concluída!")
    return state

# Nó 3: Editar vídeo
def node_editar(state: CortAIState) -> CortAIState:
    """
    Terceiro nó: o editor, corta o vídeo original baseado na análise.

    Gera múltiplos clips separados (um para cada highlight).
    """
    print("\n -> [3/3] Editando o vídeo...")

    video_id = state.get("video_id")
    celery_task = state.get("celery_task")

    # Progress: 70% - Cortando vídeo
    if video_id:
        update_progress(video_id, "editing", 70, "Cortando vídeo...")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'editing', 'percentage': 70, 'message': 'Cortando vídeo...'}
        )

    # Se já houver erro nas etapas anteriores, não tenta editar
    if state.get("error"):
        return state

    # Garante que o highlight foi gerado
    if not state.get("highlight"):
        state["error"] = "Highlight não gerado na etapa de análise."
        return state

    # Get unique paths for this video
    paths = get_video_paths(video_id)
    highlight_json_path = state.get("highlight_json_path", paths["highlight_json_path"])
    clips_dir = paths["clips_dir"]

    # Garante que o JSON existe
    if not os.path.exists(highlight_json_path):
        state["error"] = f"Arquivo de highlight não encontrado: {highlight_json_path}"
        return state

    try:
        # Executa editor - retorna lista de caminhos dos clips gerados
        clips_paths = executar_agente_editor(
            input_video=state["video_path"],
            highlight_json=highlight_json_path,
            output_dir=clips_dir,  # Diretório único para este vídeo
            transcription_path=state.get("transcription_path"),
            include_subtitles=state.get("include_subtitles", True)
        )

        if isinstance(clips_paths, str):
            clips_paths = [clips_paths]

        def normalize_path(p: str) -> str:
            p_path = Path(p)
            if p_path.is_absolute():
                return str(p_path)
            return str(Path(DATA_DIR) / p_path)

        clips_paths = [normalize_path(p) for p in clips_paths]

        # Salva lista de clips no state
        # highlight_path mantém compatibilidade (primeiro clip), mas também salvamos a lista completa
        state["highlight_path"] = clips_paths[0] if clips_paths else None
        state["clips_paths"] = clips_paths

        # Gera legendas e thumbnail do primeiro clip
        try:
            range_info = first_highlight_range(highlight_json_path)
            if range_info and state.get("transcription_path") and state.get("clips_paths"):
                clipped_transcription = build_clipped_transcription(
                    state["transcription_path"],
                    start=range_info["start"],
                    end=range_info["end"]
                )
                first_clip = state["clips_paths"][0]
                base = Path(first_clip)
                srt_path = str(base.with_suffix(".srt"))
                vtt_path = str(base.with_suffix(".vtt"))
                thumb_path = str(base.with_name(base.stem + "_thumb.jpg"))

                make_srt(clipped_transcription, srt_path)
                make_vtt(clipped_transcription, vtt_path)
                choose_thumbnail(
                    source_path=state["video_path"],
                    start_time=range_info["start"],
                    end_time=range_info["end"],
                    output_path=thumb_path,
                    strategy="middle"
                )

                state["subtitle_srt_path"] = srt_path
                state["subtitle_vtt_path"] = vtt_path
                state["thumbnail_path"] = thumb_path
        except Exception as e:
            print(f"[warn] Falha ao gerar legendas/thumbnail: {e}")

        # Progress: 95% - Finalizando
        num_clips = len(clips_paths)
        if video_id:
            update_progress(video_id, "editing", 95, f"Finalizando... {num_clips} clips gerados")
        if celery_task:
            celery_task.update_state(
                state='PROGRESS',
                meta={'stage': 'editing', 'percentage': 95, 'message': f'Finalizando... {num_clips} clips gerados'}
            )

        print(f"\n ✔ {num_clips} clip(s) gerado(s)!")
    except Exception as e:
        state["error"] = f"EditorError: {str(e)}"

    return state

# Montagem do fluxo completo

def build_graph():
    """
    Função que cria e compila o grafo do fluxo de execução
    """
    workflow = StateGraph(CortAIState)

    # Adiciona os nós
    workflow.add_node("transcrever", node_transcrever)
    workflow.add_node("analisar", node_analisar)
    workflow.add_node("editar", node_editar)

    # Define ponto de entrada
    workflow.set_entry_point("transcrever")

    # Define arestas (fluxo de execução)
    workflow.add_edge("transcrever", "analisar")
    workflow.add_edge("analisar", "editar")
    workflow.add_edge("editar", END)

    # Compila e retorna o grafo
    return workflow.compile()


# Instância do grafo para uso externo (ex.: Celery)
app = build_graph()
