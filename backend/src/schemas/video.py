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
