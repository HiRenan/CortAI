"""
Video model for storing processed videos
"""
from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum
from typing import Optional

from src.database import Base


class VideoStatus(str, enum.Enum):
    """Enum for video processing status"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Video(Base):
    """Video model for storing user videos and their processing status"""
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    status: Mapped[VideoStatus] = mapped_column(
        SQLEnum(VideoStatus),
        default=VideoStatus.PROCESSING,
        nullable=False
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    output_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="videos")

    def __repr__(self):
        return f"<Video(id={self.id}, user_id={self.user_id}, status={self.status})>"
