"""
Video processing routes with authentication and database persistence
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from celery.result import AsyncResult

from src.database import get_db
from src.models.user import User
from src.models.video import Video, VideoStatus
from src.schemas.video import VideoCreate, VideoResponse, VideoListResponse, TaskStatusResponse
from src.api.dependencies.auth import get_current_active_user
from src.core.tasks import process_video_task

router = APIRouter()


@router.post("/process", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def process_video(
    request: VideoCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new video processing request and start background task.
    Requires authentication.
    """
    # Create video record in database
    video = Video(
        user_id=current_user.id,
        url=request.url,
        status=VideoStatus.PROCESSING
    )

    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Dispatch Celery task with video_id
    task = process_video_task.delay(request.url, video.id)

    # Update video with task_id
    video.task_id = task.id
    await db.commit()
    await db.refresh(video)

    return video


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
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

    return {
        "videos": videos,
        "total": len(videos)
    }


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific video.
    Only the video owner can access it.
    """
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vídeo não encontrado"
        )

    return video


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check the status of a video processing task.
    """
    # Get video by task_id
    result = await db.execute(
        select(Video).where(
            Video.task_id == task_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task não encontrada ou não pertence ao usuário"
        )

    # Get Celery task status
    task_result = AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "video_id": video.id,
        "result": task_result.result if task_result.ready() else None,
        # Progress tracking fields from database
        "progress_stage": video.progress_stage,
        "progress_percentage": video.progress_percentage,
        "progress_message": video.progress_message
    }


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a video and its associated files.
    Only the video owner can delete it.
    """
    # Get video
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.user_id == current_user.id
        )
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vídeo não encontrado"
        )

    # Delete from database
    await db.delete(video)
    await db.commit()

    return None

