"""
Celery tasks for video processing
"""
from .celery_app import celery_app
from src.core.graph import build_graph, cleanup_video_files
from src.core.progress import update_progress
from src.database import get_sync_db
from src.models.video import Video, VideoStatus
import os


@celery_app.task(bind=True)
def process_video_task(self, url: str, video_id: int, max_highlights: int = 5):
    """
    Celery task that executes the complete LangGraph pipeline.
    Updates video status in database upon completion or failure.

    Args:
        url: Video URL to process
        video_id: Database ID of the video
        max_highlights: Maximum number of highlights to generate (default: 5)
    """
    db_session = None
    try:
        # Initial progress: 0%
        update_progress(video_id, "transcribing", 0, "Iniciando processamento...")
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'transcribing', 'percentage': 0, 'message': 'Iniciando processamento...'}
        )

        print(f"Iniciando processamento para: {url} (video_id: {video_id}, max_highlights: {max_highlights})")

        # Build and execute graph
        graph = build_graph()

        # Pass video_id, celery task instance, and max_highlights to graph state
        result = graph.invoke({
            "url": url,
            "video_id": video_id,
            "celery_task": self,
            "max_highlights": max_highlights
        })

        # Check for errors
        if result.get("error"):
            raise Exception(result["error"])

        # Final progress: 100%
        update_progress(video_id, None, 100, "Concluído!")
        self.update_state(
            state='PROGRESS',
            meta={'stage': None, 'percentage': 100, 'message': 'Concluído!'}
        )

        # Update video status to COMPLETED in database
        db_gen = get_sync_db()
        db_session = next(db_gen)

        video = db_session.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = VideoStatus.COMPLETED
            video.output_path = result.get("highlight_path")
            video.title = result.get("title")  # If available from processing
            # Clear progress fields on completion
            video.progress_stage = None
            video.progress_percentage = 100
            video.progress_message = "Concluído!"
            db_session.commit()
            print(f"Video {video_id} marked as COMPLETED")

        db_session.close()

        # Cleanup temporary files (keeps clips and JSON files for debugging)
        cleanup_video_files(video_id)

        return {
            "status": "completed",
            "video_path": result.get("highlight_path"),
            "transcription_status": "ok" if result.get("transcription") else "missing"
        }

    except Exception as e:
        print(f"Erro no processamento: {str(e)}")

        # Update progress to error state
        update_progress(video_id, None, 0, f"Erro: {str(e)[:200]}")

        # Update video status to FAILED in database
        try:
            if db_session is None:
                db_gen = get_sync_db()
                db_session = next(db_gen)

            video = db_session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = VideoStatus.FAILED
                # Clear progress on failure
                video.progress_stage = None
                video.progress_percentage = 0
                video.progress_message = f"Erro: {str(e)[:200]}"
                db_session.commit()
                print(f"Video {video_id} marked as FAILED")

            if db_session:
                db_session.close()
        except Exception as db_error:
            print(f"Erro ao atualizar status no banco: {str(db_error)}")

        # Re-raise for Celery to mark as failure
        raise e
