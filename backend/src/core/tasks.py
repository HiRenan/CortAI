from .celery_app import celery_app
from src.core.graph import build_graph
import os

@celery_app.task(bind=True)
def process_video_task(self, url: str):
    """
    Task do Celery que executa o pipeline completo do LangGraph.
    """
    try:
        # Atualiza estado inicial
        self.update_state(state='PROCESSING', meta={'status': 'Iniciando grafo...'})
        
        print(f"Iniciando processamento para: {url}")
        
        # Constrói e executa o grafo
        graph = build_graph()
        
        # O invoke é síncrono e bloqueante, ideal para rodar dentro do worker
        result = graph.invoke({"url": url})
        
        # Verifica sucesso
        if result.get("error"):
            raise Exception(result["error"])
            
        return {
            "status": "completed",
            "video_path": result.get("highlight_path"),
            "transcription_status": "ok" if result.get("transcription") else "missing"
        }
        
    except Exception as e:
        print(f"Erro no processamento: {str(e)}")
        # Relança para o Celery marcar como falha
        raise e
