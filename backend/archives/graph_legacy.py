# Importa os agentes especializados para cada etapa do processo
# CORRIGIDO: Imports relativos para funcionar dentro do pacote backend
from src.agents.transcriber import transcricao_youtube_video
from src.agents.analyst import AnalystAgent  # Novo agente com JSON/Pydantic
from src.agents.editor import executar_agente_editor

# Importa progress tracking
from src.core.progress import update_progress

# Importa configurações centralizadas
from src.core.config import DATA_DIR

# Importa funções de chunking
from src.utils.chunking import should_use_chunking

# Importa a estrutura principal do grafo (StateGraph) e o marcador de fim de fluxo (END)
from langgraph.graph import StateGraph, END

# Importa tipos para tipagem estática
from typing import TypedDict, Optional, Dict, Any
from pathlib import Path
import os

# Necessário para salvar o arquivo de cortes
import json


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
        return state

    texto_transcricao = transcription_json.get("text", "").strip()
    segments = transcription_json.get("segments", [])

    if not texto_transcricao:
        state["error"] = "Transcrição vazia ou inválida!"
        return state

    # Cria o agente analista
    agent = AnalystAgent()

    # Decide se usa chunking baseado no tamanho da transcrição
    use_chunking = should_use_chunking(texto_transcricao, threshold_chars=20000)

    if use_chunking:
        print(f"  Transcrição longa detectada ({len(texto_transcricao)} chars)")
        print(f"  Usando processamento em chunks (max_highlights={max_highlights})")

        # Verifica se temos segments (necessário para chunking)
        if not segments:
            state["error"] = "Segments não encontrados na transcrição (necessário para chunking)"
            return state

        # Usa método chunked
        highlight_output, error = agent.run_chunked(
            segments=segments,
            max_highlights=max_highlights,
            chunk_duration_seconds=360  # 6 minutos
        )
    else:
        print(f"  Transcrição normal ({len(texto_transcricao)} chars)")
        print(f"  Usando processamento direto")

        # Usa método normal
        highlight_output, error = agent.run(texto_transcricao)

    if error:
        state["error"] = f"AnalystError: {error}"
        return state

    # Salva o resultado validado
    state["highlight"] = highlight_output.dict()

    # Log dos highlights encontrados
    num_highlights = len(highlight_output.highlights)
    print(f"\n  Encontrados {num_highlights} highlights:")
    for idx, h in enumerate(highlight_output.highlights, 1):
        print(f"    {idx}. {h.start:.1f}s - {h.end:.1f}s (score: {h.score or 'N/A'})")

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
            output_dir=clips_dir  # Diretório único para este vídeo
        )

        # Salva lista de clips no state
        # highlight_path mantém compatibilidade (primeiro clip), mas também salvamos a lista completa
        state["highlight_path"] = clips_paths[0] if clips_paths else None
        state["clips_paths"] = clips_paths

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
