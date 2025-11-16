import os
import json
import subprocess
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from celery import shared_task
from openai import AsyncOpenAI


#  PROMPTS DO ANALYST AGENT

ANALYST_SYSTEM_PROMPT = """
Você é um agente avançado de Análise Multimodal especializado em identificar momentos fortes,
engraçados, emocionantes ou viralizáveis em vídeos longos.

Você deve avaliar:
- Linguagem (conteúdo, emoção, humor)
- Ritmo da narrativa
- Mudança de tópicos
- Momento de impacto ou clímax
- Reações e intenções implícitas

Regras:
- Gere cortes entre 15 e 90 segundos
- Priorize emoção, humor, relevância e momentos marcantes
- Sempre explique o motivo da seleção
"""

ANALYST_OUTPUT_FORMAT = """
Responda ESTRITAMENTE em JSON com o seguinte formato:

{
  "segments": [
    {
      "start": 0.0,
      "end": 32.5,
      "title": "Reação chocada ao plot twist",
      "score": 0.93,
      "reason": "Mudança brusca de emoção e aumento no tom de voz."
    }
  ]
}
"""


#  SCHEMAS (Analyst + Editor)

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class AnalystInput(BaseModel):
    video_id: str
    transcript: List[TranscriptSegment]
    thumbnails: Optional[List[str]] = None


class AnalystOutputSegment(BaseModel):
    start: float
    end: float
    title: str
    score: float
    reason: str


class AnalystOutput(BaseModel):
    video_id: str
    segments: List[AnalystOutputSegment]


class EditorSegment(BaseModel):
    start: float
    end: float
    title: str
    score: float
    reason: str


class EditorInput(BaseModel):
    video_id: str
    segments: List[EditorSegment]


class EditorOutput(BaseModel):
    video_id: str
    cuts: List[str]


#  ANALYST AGENT

client = AsyncOpenAI()


class AnalystAgent:

    async def analyze(self, data: AnalystInput) -> AnalystOutput:
        transcript_text = "\n".join(
            [f"[{seg.start:.2f} → {seg.end:.2f}] {seg.text}" for seg in data.transcript]
        )

        prompt = f"""
        Aqui está a transcrição com timestamps:

        {transcript_text}

        {ANALYST_OUTPUT_FORMAT}
        """

        response = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4
        )

        raw = response.choices[0].message["content"]
        parsed = json.loads(raw)

        return AnalystOutput(
            video_id=data.video_id,
            segments=parsed["segments"]
        )


async def run_analyst(data: AnalystInput) -> AnalystOutput:
    agent = AnalystAgent()
    return await agent.analyze(data)


#  EDITOR AGENT

STORAGE_PATH = "storage/editor"


class EditorAgent:

    def render_segment(self, video_path: str, start: float, end: float, out_path: str):
        duration = end - start

        command = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-vf", "scale=1080:-1",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            out_path
        ]

        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def process(self, data: EditorInput) -> EditorOutput:
        video_path = f"storage/videos/{data.video_id}.mp4"
        output_dir = f"{STORAGE_PATH}/{data.video_id}"

        os.makedirs(output_dir, exist_ok=True)

        cuts_paths = []

        for index, seg in enumerate(data.segments, start=1):
            out_file = f"{output_dir}/cut_{index:02d}.mp4"
            self.render_segment(video_path, seg.start, seg.end, out_file)
            cuts_paths.append(out_file)

        return EditorOutput(
            video_id=data.video_id,
            cuts=cuts_paths
        )


def run_editor(data: EditorInput) -> EditorOutput:
    agent = EditorAgent()
    return agent.process(data)


#  MOCK DO BANCO

def save_analyst_result(result: AnalystOutput):
    print(f"[DB] RESULTADO DO ANALISTA ► Vídeo: {result.video_id}")
    for s in result.segments:
        print(f" - Corte detectado: {s.title}")


def save_editor_output(output: EditorOutput):
    print(f"[DB] RESULTADO DO EDITOR ► Vídeo: {output.video_id}")
    for c in output.cuts:
        print(" - Arquivo gerado:", c)


#  CELERY WORKERS (Analyst → Editor)

@shared_task(bind=True)
def analyst_task(self, payload: dict):
    """
    Executa o Analyst Agent e chama automaticamente o Editor.
    """
    data = AnalystInput(**payload)

    result = asyncio.run(run_analyst(data))

    save_analyst_result(result)

    # Chama automaticamente o editor
    editor_task.delay({
        "video_id": result.video_id,
        "segments": [s.dict() for s in result.segments]
    })

    return {
        "status": "analyst_completed",
        "segments": len(result.segments)
    }


@shared_task(bind=True)
def editor_task(self, payload: dict):
    """
    Executa o Editor Agent.
    """
    data = EditorInput(**payload)

    output = run_editor(data)

    save_editor_output(output)

    return {
        "status": "editor_completed",
        "cuts": output.cuts
    }
