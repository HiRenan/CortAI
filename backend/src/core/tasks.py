from .celery_app import celery_app
from src.graphs.main_graph import app as graph_app
import time

@celery_app.task(bind=True)
def process_video_task(self, url: str):
    """
    Task do Celery que executa o pipeline completo do LangGraph (Streaming).
    """
    try:
        # Atualiza estado inicial
        self.update_state(state='PROCESSING', meta={'status': 'Iniciando grafo de streaming...'})
        
        print(f"Iniciando processamento para: {url}")
        
        # Gera um job_id único
        job_id = f"job_{int(time.time())}"
        
        # Estado inicial para o grafo
        initial_state = {
            "url": url,
            "job_id": job_id
        }
        
        # Executa o grafo
        # Como é um grafo de streaming com loop, invoke() rodará até encontrar END.
        # O grafo foi desenhado para rodar continuamente até que a análise termine ou ocorra erro.
        result = graph_app.invoke(initial_state)
        
        # Verifica erro no estado final
        if result.get("error"):
            raise Exception(result["error"])
            
        return {
            "status": "completed",
            "job_id": job_id,
            "video_path": result.get("highlight_path"),
            "transcription_chunks": len(result.get("transcription_chunks", []))
        }
        
    except Exception as e:
        print(f"Erro no processamento: {str(e)}")
        # Relança para o Celery marcar como falha
        raise e
