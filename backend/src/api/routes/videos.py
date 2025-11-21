from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.tasks import process_video_task
from celery.result import AsyncResult

router = APIRouter()

class VideoRequest(BaseModel):
    url: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.post("/process", response_model=TaskResponse)
async def process_video(request: VideoRequest):
    """
    Inicia o processamento de um vídeo em background.
    """
    # Dispara a task do Celery
    task = process_video_task.delay(request.url)
    
    return {
        "task_id": task.id,
        "status": "processing"
    }

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Verifica o status de uma tarefa.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    
    return response

