"""
Progress tracking helper for video processing
"""
from src.database import get_sync_db
from src.models.video import Video


def update_progress(
    video_id: int,
    stage: str,
    percentage: int,
    message: str
) -> None:
    """
    Update video progress fields in the database.

    Args:
        video_id: Video ID to update
        stage: Current stage ('transcribing', 'analyzing', 'editing')
        percentage: Progress percentage (0-100)
        message: Descriptive message for the current operation
    """
    db_gen = get_sync_db()
    db_session = next(db_gen)
    try:
        video = db_session.query(Video).filter(Video.id == video_id).first()
        if video:
            video.progress_stage = stage
            video.progress_percentage = percentage
            video.progress_message = message
            db_session.commit()
    except Exception as e:
        print(f"Error updating progress for video {video_id}: {e}")
        db_session.rollback()
    finally:
        db_session.close()
