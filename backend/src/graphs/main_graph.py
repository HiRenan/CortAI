# Importa os agentes especializados para cada etapa do processo
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from src.agents.transcriber import transcricao_youtube_video, transcrever_video_local
from src.agents.analyst import executar_agente_analista
from src.agents.editor import executar_agente_editor, _normalize_highlights
from src.agents.collector_streams import executar_agente_coletor
from src.agents.screenwriter import make_srt, make_vtt, choose_thumbnail
from src.core.progress import update_progress

# Importa a estrutura principal do grafo (StateGraph) e o marcador de fim de fluxo (END)
from langgraph.graph import StateGraph, END 

# Importa tipos para tipagem estática 
from typing import TypedDict, Optional 

# Necessário para salvar o arquivo de cortes
import json 

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


def concat_segments_ffmpeg(segment_paths: List[str], output_path: str) -> str:
    """
    Concatena segmentos em um único mp4 usando ffmpeg concat demuxer.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    list_file = output_path + ".concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            f.write(f"file '{p}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Saída do ffmpeg concat:", result.stderr)
        raise RuntimeError("Erro ao concatenar segmentos com ffmpeg")
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
        print(f"[warn] Não foi possível ler highlights para subtítulos/thumbnail: {e}")
        return None


def build_clipped_transcription(transcription_path: str, start: float, end: float) -> Dict[str, Any]:
    """
    Filtra e normaliza segments para o intervalo do highlight, deslocando timestamps para começar em 0.
    """
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


# --------------------------------------------------------------------------------------------------------------------------------------
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
    video_id: Optional[int]

# --------------------------------------------------------------------------------------------------------------------------------------
# Definindo os nós (estações de trabalho) - O nó recebe algo -> processa -> retorna o estado atualizado
# --------------------------------------------------------------------------------------------------------------------------------------

def node_transcrever(state: CortAIState) -> CortAIState: 
    """
    Primeiro nó: responsável por baixar o vídeo e gerar a transcrição (Whisper)
    """
    print("\n -> [1/3] Transcrevendo vídeo...\n")

    # Extrai a URL do estado atual 
    url = state["url"]
    video_id = state.get("video_id")

    # Define os caminhos temporários para os arquivos 
    video_path = "backend/data/temp_video.mp4"
    transcription_path = "backend/data/transcricao_temp.json"

    if video_id:
        update_progress(video_id, "transcribing", 10, "Baixando vídeo...")

    # Decide se deve capturar stream antes de transcrever
    use_collector = should_collect_stream(url)

    if use_collector:
        segments_dir = "backend/data/stream_segments"
        os.makedirs(segments_dir, exist_ok=True)
        print(f"Detectado stream. Coletando segmentos em {segments_dir}...")
        collect_result = executar_agente_coletor(
            stream_url=url,
            output_dir=segments_dir,
            segment_duration=60,
            max_duration=300
        )
        if not collect_result or not collect_result.get("segment_paths"):
            state["error"] = "Falha na coleta do stream."
            return state

        segment_paths = collect_result["segment_paths"]
        try:
            video_path = concat_segments_ffmpeg(segment_paths, video_path)
        except Exception as e:
            state["error"] = f"Erro ao concatenar segmentos: {e}"
            return state

        transcription = transcrever_video_local(
            video_path=video_path,
            output_json_path=transcription_path
        )
    else:
        # Chama o agente transcritor 
        transcription = transcricao_youtube_video(url=url, temp_video_path=video_path, output_json_path=transcription_path)

    # Atualiza o estado com as novas informações obtidas
    state["video_path"] = video_path                      # Onde o mp4 está
    state["transcription_path"] = transcription_path       # Onde o JSON está 
    state["transcription"] = transcription                # O conteúdo do texto

    if transcription:
        print("\n ✔ Transcrição concluída!")
        if video_id:
            update_progress(video_id, "transcribing", 35, "Transcrição concluída")
    else:
        print("\n ❌ Transcrição falhou. Interrompendo o fluxo.")
        state["error"] = "Falha na transcrição ou download do vídeo."
        if video_id:
            update_progress(video_id, "transcribing", 0, "Falha na transcrição ou download do vídeo.")

    return state

# --------------------------------------------------------------------------------------------------------------------------------------

def node_analisar(state: CortAIState) -> CortAIState:
    """
    Segundo nó: o 'cérebro'. Lê a transcrição e decide o que é importante
    """
    print("\n -> [2/3] Analisando transcrição...")
    video_id = state.get("video_id")

    if video_id:
        update_progress(video_id, "analyzing", 50, "Analisando transcrição...")

    # Recupera o caminho da transcrição salvo no nó anterior
    transcription_path = state["transcription_path"]

    # Define o caminho de saída para o arquivo de highlights
    output_path = "backend/data/highlight.json"

    # Chama o agente analista com ambos os parâmetros
    highlight = executar_agente_analista(input_json=transcription_path, output_json=output_path)

    # Guarda a decisão da LLM de corte no estado
    state["highlight"] = highlight

    print(f"\nArquivo de corte salvo em: {output_path}")
    print("\n ✔ Análise concluída!")
    if video_id:
        update_progress(video_id, "analyzing", 70, "Análise concluída")

    return state 

# --------------------------------------------------------------------------------------------------------------------------------------

def node_editar(state: CortAIState) -> CortAIState: 
    """
    Terceiro nó: o editor, corta o vídeo original baseado na análise
    """
    print("\n -> [3/3] Editando o vídeo...")
    video_id = state.get("video_id")

    if video_id:
        update_progress(video_id, "editing", 80, "Cortando vídeo...")

    # Define onde os vídeos finais serão salvos 
    clips_dir = "backend/data/clips"

    # Chama o agente editor
    result_path = executar_agente_editor(
        input_video=state["video_path"],
        highlight_json="backend/data/highlight.json",
        output_dir=clips_dir
    )

    # Atualiza o estado com o caminho do produto final
    if isinstance(result_path, list):
        state["highlight_path"] = result_path[0] if result_path else None
        state["clips_paths"] = result_path
    else:
        state["highlight_path"] = result_path
        state["clips_paths"] = [result_path] if result_path else []

    if video_id:
        update_progress(video_id, "editing", 95, "Finalizando cortes...")

    # Gera legendas/thumbnail do primeiro highlight para o primeiro clip
    try:
        range_info = first_highlight_range("backend/data/highlight.json")
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

    print("\n ✔ Highlight gerado!")

    return state


# --------------------------------------------------------------------------------------------------------------------------------------
def node_planner(state: CortAIState) -> CortAIState:
    """
    Nó planner: chama o CrewAI para obter um plano (highlights + editor_params), valida
    e injeta os highlights no estado. Também persiste um `highlight.json` compatível
    com o agente editor para que o fluxo existente não precise mudar.
    """
    print("\n -> [PLANNER] Gerando plano via CrewAI (se habilitado)...")

    plan = plan_job(state)

    highlights = plan.get("highlights") if isinstance(plan, dict) else None
    if not highlights:
        # Se não houver highlights retornados, mantenha o que o analyst produziu
        existing = state.get("highlight")
        if isinstance(existing, dict) and "highlights" in existing:
            highlights = existing.get("highlights", [])
        else:
            highlights = []

    # Sanitize highlights: ensure numeric start/end and minimum duration
    sanitized = []
    MIN_DUR = float(os.getenv("CREWAI_MIN_HIGHLIGHT_SECONDS", "5"))
    for h in highlights:
        try:
            start = float(h.get("start", h.get("inicio", 0)))
            end = float(h.get("end", h.get("fim", start + MIN_DUR)))
        except Exception:
            continue
        if end <= start:
            end = start + MIN_DUR
        if start < 0:
            start = 0.0
        summary = h.get("summary", h.get("resumo", ""))
        score = h.get("score", h.get("pontuacao", 0))
        sanitized.append({"start": start, "end": end, "summary": summary, "score": score})

    # Injeta no estado no formato esperado pelo editor (mantendo compatibilidade)
    state["highlight"] = {"highlights": sanitized}
    state["highlights"] = sanitized
    state["editor_params"] = plan.get("editor_params", {}) if isinstance(plan, dict) else {}

    # Grava o arquivo highlight.json na pasta padrão para o editor ler
    try:
        job_id = state.get("job_id") or state.get("url", "no_job")
        # Prefer job-specific path quando disponível
        if "job_id" in state and state.get("job_id"):
            out_dir = f"backend/data/jobs/{state.get('job_id')}/highlights"
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "highlight.json")
        else:
            out_path = "backend/data/highlight.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"highlights": sanitized}, f, ensure_ascii=False, indent=4)
        print(f"\n[PLANNER] highlight.json salvo em: {out_path}")
    except Exception as e:
        print(f"[PLANNER] Aviso: não foi possível salvar highlight.json: {e}")

    return state

# --------------------------------------------------------------------------------------------------------------------------------------

# Montagem do fluxo 
def build_graph(): 
    """
    Função que cria e compila o grafo do fluxo de execução
    """

    # Inicializa o grafo passando a definição de tipagem do estado 
    workflow = StateGraph(CortAIState)

    # Adiciona os nós 
    workflow.add_node("transcrever", node_transcrever)
    workflow.add_node("analisar", node_analisar)
    workflow.add_node("editar", node_editar)

    # Define onde o fluxo começa 
    workflow.set_entry_point("transcrever")

    # Define as arestas (o caminho que a informação percorre)
    # Define a lógica de roteamento (condicional)
    workflow.add_conditional_edges(
        "transcrever",
        lambda state: "analisar" if state.get("transcription") else END,
        {"analisar": "analisar", END: END}
    )
    workflow.add_edge("analisar", "editar")
    workflow.add_edge("editar", END)

    # Compila o grafo
    return workflow.compile()

# --------------------------------------------------------------------------------------------------------------------------------------
# Cria a instância do grafo compilado para ser usado em tasks.py
app = build_graph()
