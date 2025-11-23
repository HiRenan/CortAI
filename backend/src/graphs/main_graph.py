# Importa os agentes especializados para cada etapa do processo
from src.agents.transcriber import transcricao_youtube_video
from src.agents.analyst import executar_agente_analista
from src.agents.editor import executar_agente_editor
from src.services.crewai_client import plan_job

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

    # Define os caminhos temporários para os arquivos 
    video_path = "backend/data/temp_video.mp4"
    transcription_path = "backend/data/transcricao_temp.json"

    # Chama o agente transcritor 
    transcription = transcricao_youtube_video(url=url, temp_video_path=video_path, output_json_path=transcription_path)

    # Atualiza o estado com as novas informações obtidas
    state["video_path"] = video_path                      # Onde o mp4 está
    state["transcription_path"] = transcription_path       # Onde o JSON está 
    state["transcription"] = transcription                # O conteúdo do texto

    if transcription:
        print("\n ✔ Transcrição concluída!")
    else:
        print("\n ❌ Transcrição falhou. Interrompendo o fluxo.")
        state["error"] = "Falha na transcrição ou download do vídeo."

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
    highlight = executar_agente_analista(input_json=transcription_path)

    # Guarda a decisão da LLM de corte no estado
    state["highlight"] = highlight

    # Salva o arquivo para o agente editor ler
    output_path = "backend/data/highlight.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(highlight, f, indent=4, ensure_ascii=False)
    print(f"\nArquivo de corte salvo em: {output_path}")

    print("\n ✔ Análise concluída!")

    return state 

# --------------------------------------------------------------------------------------------------------------------------------------

def node_editar(state: CortAIState) -> CortAIState: 
    """
    Terceiro nó: o editor, corta o vídeo original baseado na análise
    """
    print("\n -> [3/3] Editando o vídeo...")

    # Define onde o vídeo final será salvo 
    highlight_path = "backend/data/highlight.mp4"

    # Chama o agente editor 
    result_path = executar_agente_editor(
        input_video=state["video_path"], 
        highlight_json="backend/data/highlight.json", 
        output_video=highlight_path
    )

    # Atualiza o estado com o caminho do produto final 
    state["highlight_path"] = result_path

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


# Expose a compiled graph as `app` so other modules (e.g. Celery tasks)
# can import it with `from src.graphs.main_graph import app`.
app = build_graph()