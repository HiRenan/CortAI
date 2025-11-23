"""
Video schemas for request/response validation
"""
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
from src.models.video import VideoStatus


class VideoCreate(BaseModel):
    """Schema for creating a new video processing request"""
    url: str = Field(
        description="URL of the video to process (YouTube, Twitch, etc.)"
    )
    max_highlights: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of highlights to generate (1-20, default: 5)"
    )


class VideoResponse(BaseModel):
    """Schema for video response"""
    id: int
    user_id: int
    url: str
    title: Optional[str] = None
    status: VideoStatus
    task_id: Optional[str] = None
    output_path: Optional[str] = None
    created_at: datetime

    # Progress tracking fields
    progress_stage: Optional[str] = None
    progress_percentage: Optional[int] = None
    progress_message: Optional[str] = None

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """Schema for list of videos"""
    videos: list[VideoResponse]
    total: int


class TaskStatusResponse(BaseModel):
    """Schema for task status response"""
    task_id: str
    status: str
    video_id: Optional[int] = None
    result: Optional[dict] = None

    # Progress tracking fields
    progress_stage: Optional[str] = None
    progress_percentage: Optional[int] = None
    progress_message: Optional[str] = None
