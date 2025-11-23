from fastapi import FastAPI
import logging
import sys

log = logging.getLogger("backend.main")


app = FastAPI(title="CortAI API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "CortAI", "status": "running"}


# The interactive CLI mode is provided below. Heavy imports are performed
# inside functions or under `if __name__ == '__main__'` to avoid import-time
# side-effects when the module is loaded by the ASGI server.

import uuid


def detect_content_type(url: str) -> str:
    url_lower = url.lower()
    if '.m3u8' in url_lower or 'manifest' in url_lower:
        return 'stream'
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    if 'twitch.tv' in url_lower:
        return 'stream'
    return 'video'


def print_banner():
    print("\n" + "=" * 70)
    print("CORTAI - Processamento Inteligente de Vídeos e Streams")
    print("=" * 70)
    print()


def get_url_from_user() -> str:
    try:
        url = input("URL: ").strip()
        return url
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0)


def ask_youtube_type() -> str:
    try:
        choice = input("Este link é [1] vídeo gravado ou [2] live stream? [1/2]: ").strip()
        return 'stream' if choice == '2' else 'video'
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0)


def get_stream_parameters() -> dict:
    try:
        segment_input = input("Duração do segmento em segundos [30]: ").strip()
        segment_duration = int(segment_input) if segment_input else 30
        max_input = input("Duração máxima em segundos [120]: ").strip()
        max_duration = int(max_input) if max_input else 120
        return {'segment_duration': segment_duration, 'max_duration': max_duration}
    except (EOFError, KeyboardInterrupt):
        print("\n\nOperação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0)


def process_video(url: str, job_id: str):
    # Local imports to avoid ASGI import-time side-effects
    from src.services.messaging_rabbit import new_job, publish, TRANSCRIBE_QUEUE
    from src.services.state_manager import initialize_job

    print("Processando vídeo gravado...\n")
    initialize_job(job_id, url)
    msg = new_job(step="transcribe", job_id=job_id, payload={"url": url})
    publish(TRANSCRIBE_QUEUE, msg)
    print(f"Job {job_id} publicado na fila de transcrição.")


def process_stream(url: str, job_id: str, params: dict):
    from src.services.messaging_rabbit import new_job, publish, COLLECT_QUEUE
    from src.services.state_manager import initialize_job

    print("Processando live stream...\n")
    initialize_job(job_id, url)
    msg = new_job(
        step="collect",
        job_id=job_id,
        payload={
            "stream_url": url,
            "segment_duration": params['segment_duration'],
            "max_duration": params['max_duration']
        }
    )
    publish(COLLECT_QUEUE, msg)
    print(f"Job {job_id} publicado na fila de coleta.")


def main():
    # CLI entrypoint
    print_banner()
    url = get_url_from_user()
    if not url:
        print("Erro: URL não pode estar vazia!")
        sys.exit(1)
    content_type = detect_content_type(url)
    if content_type == 'youtube':
        content_type = ask_youtube_type()
    job_id = uuid.uuid4().hex[:12]
    if content_type == 'stream':
        params = get_stream_parameters()
        confirm = input("Deseja processar este stream? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada pelo usuário.")
            sys.exit(0)
        process_stream(url, job_id, params)
    else:
        confirm = input("Deseja processar este vídeo? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada pelo usuário.")
            sys.exit(0)
        process_video(url, job_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        log = logging.getLogger("backend.main")
        log.exception(f"Erro ao processar: {e}")
        sys.exit(1)
