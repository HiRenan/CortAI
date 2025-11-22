# Importa os agentes especializados para cada etapa do processo
# CORRIGIDO: Imports relativos para funcionar dentro do pacote backend
from src.agents.transcriber import transcricao_youtube_video
from src.agents.analyst import AnalystAgent  # Novo agente com JSON/Pydantic
from src.agents.editor import executar_agente_editor

# Importa progress tracking
from src.core.progress import update_progress

# Importa configurações centralizadas
from src.core.config import (
    TEMP_VIDEO_PATH,
    TEMP_TRANSCRIPTION_PATH,
    TEMP_HIGHLIGHT_JSON_PATH,
    TEMP_HIGHLIGHT_VIDEO_PATH
)

# Importa a estrutura principal do grafo (StateGraph) e o marcador de fim de fluxo (END)
from langgraph.graph import StateGraph, END

# Importa tipos para tipagem estática
from typing import TypedDict, Optional, Dict, Any

# Necessário para salvar o arquivo de cortes
import json 

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


# Nó 1: Transcrever vídeo
def node_transcrever(state: CortAIState) -> CortAIState:
    """
    Primeiro nó: responsável por baixar o vídeo e gerar a transcrição (Whisper)
    """
    print("\n -> [1/3] Transcrevendo vídeo...\n")

    video_id = state.get("video_id")
    celery_task = state.get("celery_task")
    url = state["url"]

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
        temp_video_path=TEMP_VIDEO_PATH,
        output_json_path=TEMP_TRANSCRIPTION_PATH
    )

    state["video_path"] = TEMP_VIDEO_PATH
    state["transcription_path"] = TEMP_TRANSCRIPTION_PATH
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
    Segundo nó: o 'cérebro'. Lê a transcrição e decide o que é importante
    """
    print("\n -> [2/3] Analisando transcrição...")

    video_id = state.get("video_id")
    celery_task = state.get("celery_task")

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

    # Carrega a transcrição do arquivo
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription_json = json.load(f)
    except Exception as e:
        state["error"] = f"Falha ao carregar transcrição: {str(e)}"
        return state

    texto_transcricao = transcription_json.get("text", "").strip()
    if not texto_transcricao:
        state["error"] = "Transcrição vazia ou inválida!"
        return state

    # Cria o agente analista e executa
    agent = AnalystAgent()
    highlight_output, error = agent.run(texto_transcricao)

    if error:
        state["error"] = f"AnalystError: {error}"
        return state

    # Salva o resultado validado
    state["highlight"] = highlight_output.dict()

    # Salva JSON para o editor
    try:
        with open(TEMP_HIGHLIGHT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(state["highlight"], f, indent=4, ensure_ascii=False)
        print(f"\nArquivo de corte salvo em: {TEMP_HIGHLIGHT_JSON_PATH}")
    except Exception as e:
        state["error"] = f"Erro ao salvar highlight JSON: {str(e)}"
        return state

    # Progress: 66% - Análise concluída
    if video_id:
        update_progress(video_id, "analyzing", 66, "Análise concluída")
    if celery_task:
        celery_task.update_state(
            state='PROGRESS',
            meta={'stage': 'analyzing', 'percentage': 66, 'message': 'Análise concluída'}
        )

    print("\n ✔ Análise concluída!")
    return state

# Nó 3: Editar vídeo
def node_editar(state: CortAIState) -> CortAIState:
    """
    Terceiro nó: o editor, corta o vídeo original baseado na análise
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

    try:
        result_path = executar_agente_editor(
            input_video=state["video_path"],
            highlight_json=TEMP_HIGHLIGHT_JSON_PATH,
            output_video=TEMP_HIGHLIGHT_VIDEO_PATH
        )
        state["highlight_path"] = result_path

        # Progress: 95% - Finalizando
        if video_id:
            update_progress(video_id, "editing", 95, "Finalizando...")
        if celery_task:
            celery_task.update_state(
                state='PROGRESS',
                meta={'stage': 'editing', 'percentage': 95, 'message': 'Finalizando...'}
            )

        print("\n ✔ Highlight gerado!")
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
