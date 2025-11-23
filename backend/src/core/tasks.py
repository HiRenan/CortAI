from .celery_app import celery_app
from src.core.graph import app as graph_app
from src.database import get_sync_db
from src.models.video import Video, VideoStatus
import time
import re

@celery_app.task(bind=True)
def process_video_task(self, url: str, video_id: int, max_highlights: int = 5, include_subtitles: bool = True, subtitle_style: str = "youtube"):
    """
    Task do Celery que executa o pipeline completo do LangGraph.

    Args:
        url: URL do vídeo para processar
        video_id: ID do vídeo no banco de dados
        max_highlights: Número máximo de highlights a gerar
        include_subtitles: Se True, adiciona legendas burned-in nos clips
        subtitle_style: Estilo das legendas ('youtube' por padrão)
    """
    try:
        # Atualiza estado inicial
        self.update_state(state='PROCESSING', meta={'status': 'Iniciando processamento...'})

        print(f"Iniciando processamento para video_id={video_id}, url={url}, max_highlights={max_highlights}")

        # Atualiza vídeo no banco
        with next(get_sync_db()) as db:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.progress_stage = "Iniciando"
                video.progress_percentage = 10
                video.progress_message = "Preparando processamento..."
                db.commit()

        # Estado inicial para o grafo
        initial_state = {
            "url": url,
            "max_highlights": max_highlights,
            "video_id": video_id,
            "include_subtitles": include_subtitles,
            "subtitle_style": subtitle_style
        }

        # Executa o grafo
        result = graph_app.invoke(initial_state)

        # Verifica erro no estado final
        if result.get("error"):
            # Atualiza vídeo como falha
            with next(get_sync_db()) as db:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.FAILED
                    video.progress_message = f"Erro: {result['error']}"
                    db.commit()
            raise Exception(result["error"])

        # Atualiza vídeo como completo
        with next(get_sync_db()) as db:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                # Deriva título a partir do primeiro highlight se não houver
                title = video.title
                highlight_data = result.get("highlight") or {}
                if not title:
                    try:
                        if isinstance(highlight_data, list):
                            highlights = highlight_data
                        elif isinstance(highlight_data, dict) and "highlights" in highlight_data:
                            highlights = highlight_data.get("highlights") or []
                        else:
                            highlights = []

                        if highlights and isinstance(highlights, list):
                            first = highlights[0]
                            summary = first.get("summary") or first.get("resumo") or first.get("text") or ""
                            if summary:
                                title = summary[:120]
                        elif isinstance(highlight_data, dict):
                            # fallback para formato simples (sem lista)
                            summary = (
                                highlight_data.get("summary")
                                or highlight_data.get("resumo")
                                or highlight_data.get("resposta_bruta")
                                or ""
                            )
                            if summary:
                                title = summary[:120]
                    except Exception:
                        pass
                    # fallback: tenta ler do arquivo highlight.json salvo
                    try:
                        if not title and video.output_path:
                            import os, json
                            # o highlight json fica paralelo ao temp_video em data/highlight.json no grafo simples
                            path_json = "backend/data/highlight.json"
                            if os.path.exists(path_json):
                                with open(path_json, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                    if isinstance(data, dict):
                                        hs = data.get("highlights") or []
                                    elif isinstance(data, list):
                                        hs = data
                                    else:
                                        hs = []
                                    if hs:
                                        summary = hs[0].get("summary") or hs[0].get("resumo") or ""
                                        if summary:
                                            title = summary[:120]
                    except Exception:
                        pass

                # Gera thumbnail padrão do YouTube se não houver
                thumb = video.thumbnail_path
                if not thumb:
                    yt_id = None
                    try:
                        # suporta youtube.com/watch?v= e youtu.be/ID
                        m = re.search(r"v=([A-Za-z0-9_-]{6,})", url)
                        if m:
                            yt_id = m.group(1)
                        else:
                            m2 = re.search(r"youtu\\.be/([A-Za-z0-9_-]{6,})", url)
                            if m2:
                                yt_id = m2.group(1)
                    except Exception:
                        yt_id = None

                    if yt_id:
                        thumb = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"

                video.status = VideoStatus.COMPLETED
                video.progress_stage = "Concluído"
                video.progress_percentage = 100
                video.progress_message = "Processamento finalizado!"
                video.output_path = result.get("highlight_path", "")
                if title:
                    video.title = title
                if thumb:
                    video.thumbnail_path = thumb
                db.commit()

        return {
            "status": "completed",
            "video_id": video_id,
            "video_path": result.get("highlight_path"),
        }

    except Exception as e:
        print(f"Erro no processamento do video_id={video_id}: {str(e)}")

        # Marca vídeo como falha
        try:
            with next(get_sync_db()) as db:
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.FAILED
                    video.progress_message = f"Erro: {str(e)}"
                    db.commit()
        except:
            pass

        # Relança para o Celery marcar como falha
        raise e
