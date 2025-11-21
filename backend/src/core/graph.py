# Importa os agentes especializados para cada etapa do processo
# CORRIGIDO: Imports relativos para funcionar dentro do pacote backend
from src.agents.transcriber import transcricao_youtube_video
from src.agents.analyst import executar_agente_analista
from src.agents.editor import executar_agente_editor

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

    # Chama o agente transcritor usando paths centralizados
    transcription = transcricao_youtube_video(
        url=url,
        temp_video_path=TEMP_VIDEO_PATH,
        output_json_path=TEMP_TRANSCRIPTION_PATH
    )

    # Atualiza o estado com as novas informações obtidas
    state["video_path"] = TEMP_VIDEO_PATH
    state["transcription_path"] = TEMP_TRANSCRIPTION_PATH
    state["transcription"] = transcription

    print("\n ✔ Transcrição concluída!")

    return state

# --------------------------------------------------------------------------------------------------------------------------------------

def node_analisar(state: CortAIState) -> CortAIState:
    """
    Segundo nó: o 'cérebro'. Lê a transcrição e decide o que é importante
    """
    print("\n -> [2/3] Analisando transcrição...")

    # Recupera o caminho da transcrição salvo no nó anterior
    transcription_path = state["transcription_path"]

    # Chama o agente analista
    highlight = executar_agente_analista(transcription_path)

    # Guarda a decisão da LLM de corte no estado
    state["highlight"] = highlight

    # Salva o arquivo para o agente editor ler
    with open(TEMP_HIGHLIGHT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(highlight, f, indent=4, ensure_ascii=False)
    print(f"\nArquivo de corte salvo em: {TEMP_HIGHLIGHT_JSON_PATH}")

    print("\n ✔ Análise concluída!")

    return state 

# --------------------------------------------------------------------------------------------------------------------------------------

def node_editar(state: CortAIState) -> CortAIState:
    """
    Terceiro nó: o editor, corta o vídeo original baseado na análise
    """
    print("\n -> [3/3] Editando o vídeo...")

    # Chama o agente editor usando paths centralizados
    result_path = executar_agente_editor(
        input_video=state["video_path"],
        highlight_json=TEMP_HIGHLIGHT_JSON_PATH,
        output_video=TEMP_HIGHLIGHT_VIDEO_PATH
    )

    # Atualiza o estado com o caminho do produto final
    state["highlight_path"] = result_path

    print("\n ✔ Highlight gerado!")

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
    workflow.add_edge("transcrever", "analisar")
    workflow.add_edge("analisar", "editar")
    workflow.add_edge("editar", END)

    # Compila o grafo 
    return workflow.compile()

