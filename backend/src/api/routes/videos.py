"""
Video processing routes with authentication and database persistence.
"""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from celery.result import AsyncResult

from src.api.dependencies.auth import get_current_active_user
from src.core.celery_app import celery_app
from src.core.tasks import process_video_task
from src.core.config import DATA_DIR
from src.database import get_db
from src.models.user import User
from src.models.video import Video, VideoStatus
from src.schemas.video import (
    TaskStatusResponse,
    VideoCreate,
    VideoListResponse,
    VideoResponse,
)

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/process", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def process_video(
    request: VideoCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new video processing request and start background task.
    Requires authentication.
    """
    video = Video(
        user_id=current_user.id,
        url=request.url,
        status=VideoStatus.PROCESSING,
    )

    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Pass max_highlights to task (default: 5)
    max_highlights = request.max_highlights or 5
    task = process_video_task.delay(request.url, video.id, max_highlights)

    video.task_id = task.id
    await db.commit()
    await db.refresh(video)

    return video


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all videos for the authenticated user.
    """
    result = await db.execute(
        select(Video)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
    )
    videos = result.scalars().all()

    return {"videos": videos, "total": len(videos)}


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific video. Only the owner can access it.
    """
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video nao encontrado",
        )

    return video


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check the status of a video processing task.
    Uses the configured Celery app so the result backend is available.
    """
    result = await db.execute(
        select(Video).where(Video.task_id == task_id, Video.user_id == current_user.id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task nao encontrada ou nao pertence ao usuario",
        )

    # Default to a DB-derived state if Celery is unreachable or unconfigured
    status_fallback = {
        VideoStatus.PROCESSING: "PENDING",
        VideoStatus.COMPLETED: "SUCCESS",
        VideoStatus.FAILED: "FAILURE",
    }
    task_status = status_fallback.get(video.status, "PENDING")
    raw_result = None

    try:
        task_result = AsyncResult(task_id, app=celery_app)
        task_status = task_result.status

        if task_result.ready():
            res = task_result.result
            if isinstance(res, Exception):
                raw_result = {"error": str(res)}
            elif isinstance(res, dict):
                raw_result = res
            else:
                raw_result = {"result": str(res)}
    except Exception as exc:  # pragma: no cover - defensive guardrail for Celery issues
        log.warning("Could not fetch Celery status for task %s: %s", task_id, exc)

    return {
        "task_id": task_id,
        "status": task_status,
        "video_id": video.id,
        "result": raw_result,
        "progress_stage": video.progress_stage,
        "progress_percentage": video.progress_percentage,
        "progress_message": video.progress_message,
    }


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a video and its associated files. Only the owner can delete it.
    """
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video nao encontrado",
        )

    await db.delete(video)
    await db.commit()

    return None


@router.get("/{video_id}/download")
async def download_video_clip(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download the first clip of a processed video. Only the owner can download it.
    """
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video não encontrado",
        )

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video ainda não foi processado ou falhou",
        )

    if not video.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caminho do clip não encontrado",
        )

    # Construct the full path to the clip
    # output_path is like: /data/video_11/clips/clip_01_inicio_0s_duracao_15s.mp4
    clip_path = Path(video.output_path)

    # Check if file exists
    if not clip_path.exists():
        log.error(f"Clip file not found: {clip_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo de clip não encontrado no servidor",
        )

    # Extract filename for download
    filename = clip_path.name

    # Return file for download
    return FileResponse(
        path=str(clip_path),
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
