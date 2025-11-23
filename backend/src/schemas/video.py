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
    use_stream_collector: Optional[bool] = Field(
        default=False,
        description="Force stream collector (FFmpeg + yt-dlp) for lives/RTMP/HLS even when URL is not auto-detected"
    )
    stream_segment_duration: Optional[int] = Field(
        default=60,
        ge=10,
        le=600,
        description="Segment duration (seconds) when capturing a live stream"
    )
    stream_max_duration: Optional[int] = Field(
        default=300,
        ge=30,
        le=3600,
        description="Total capture duration (seconds) when recording a live stream"
    )
    max_highlights: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of highlights to generate (1-20, default: 5)"
    )
    include_subtitles: Optional[bool] = Field(
        default=True,
        description="Include burned-in subtitles in the generated clips (default: True)"
    )
    subtitle_style: Optional[str] = Field(
        default="youtube",
        description="Subtitle style: 'youtube' for classic style with black background (default: 'youtube')"
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
    thumbnail_path: Optional[str] = None
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

    # Video DB fields
    video_status: Optional[VideoStatus] = None
    output_path: Optional[str] = None

    # Progress tracking fields
    progress_stage: Optional[str] = None
    progress_percentage: Optional[int] = None
    progress_message: Optional[str] = None
