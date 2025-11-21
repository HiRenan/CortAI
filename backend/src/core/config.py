"""
Configuration module for CortAI
Centralizes paths and environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent  # project root

# Storage directories (for final outputs)
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_VIDEOS = STORAGE_DIR / "videos"
STORAGE_CLIPS = STORAGE_DIR / "clips"
STORAGE_THUMBNAILS = STORAGE_DIR / "thumbnails"
STORAGE_TEMP = STORAGE_DIR / "temp"

# Data directory (for intermediate processing)
DATA_DIR = ROOT_DIR / "data"

# Ensure directories exist
for directory in [STORAGE_DIR, STORAGE_VIDEOS, STORAGE_CLIPS, STORAGE_THUMBNAILS, STORAGE_TEMP, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Default file paths for processing
TEMP_VIDEO_PATH = str(DATA_DIR / "temp_video.mp4")
TEMP_TRANSCRIPTION_PATH = str(DATA_DIR / "transcricao_temp.json")
TEMP_HIGHLIGHT_JSON_PATH = str(DATA_DIR / "highlight.json")
TEMP_HIGHLIGHT_VIDEO_PATH = str(DATA_DIR / "highlight.mp4")

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# Validate critical environment variables
if not GOOGLE_API_KEY:
    raise ValueError("ERRO: variável GOOGLE_API_KEY não encontrada no .env!")
