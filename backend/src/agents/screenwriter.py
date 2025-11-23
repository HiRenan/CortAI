import os
import json
import subprocess

def _ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

def make_srt(transcription_source, output_path: str):
    data = transcription_source
    if isinstance(transcription_source, str):
        with open(transcription_source, "r", encoding="utf-8") as f:
            data = json.load(f)
    segments = data.get("segments", [])
    _ensure_dir(output_path)

    def fmt(t: float):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 0.5))
            text = str(seg.get("text", "")).strip()
            if end <= start:
                end = start + 0.5
            f.write(f"{i}\n")
            f.write(f"{fmt(start)} --> {fmt(end)}\n")
            f.write(text + "\n\n")
    return output_path

def make_vtt(transcription_source, output_path: str):
    data = transcription_source
    if isinstance(transcription_source, str):
        with open(transcription_source, "r", encoding="utf-8") as f:
            data = json.load(f)
    segments = data.get("segments", [])
    _ensure_dir(output_path)

    def fmt(t: float):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 0.5))
            text = str(seg.get("text", "")).strip()
            if end <= start:
                end = start + 0.5
            f.write(f"{fmt(start)} --> {fmt(end)}\n")
            f.write(text + "\n\n")
    return output_path

def choose_thumbnail(source_path: str, start_time: float, end_time: float, output_path: str, strategy: str = "middle", width: int | None = None, height: int | None = None):
    _ensure_dir(output_path)
    if strategy == "start":
        ts = float(start_time)
    elif strategy == "end":
        ts = float(end_time)
    else:
        dur = max(0.0, float(end_time) - float(start_time))
        ts = float(start_time) + dur / 2.0

    vf = []
    if width and height:
        vf.append(f"scale={int(width)}:{int(height)}:force_original_aspect_ratio=decrease")
    vf_arg = []
    if vf:
        vf_arg = ["-vf", ",".join(vf)]

    cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", source_path, *vf_arg, "-vframes", "1", output_path]
    subprocess.run(cmd, capture_output=True)
    return output_path

def get_subtitle_style_youtube() -> str:
    """
    Returns FFmpeg subtitle filter style for YouTube/TikTok appearance.

    Style characteristics:
    - Font: Arial (fallback to Sans)
    - Size: 18pt (readable on mobile)
    - Color: White text with black outline
    - Background: Semi-transparent black box
    - Position: Bottom center with margin

    Returns:
        str: FFmpeg force_style parameter string
    """
    return (
        "FontName=Arial,"
        "FontSize=18,"
        "PrimaryColour=&HFFFFFF,"      # White text
        "OutlineColour=&H000000,"      # Black outline
        "Outline=1,"                   # 1px outline thickness
        "BackColour=&H80000000,"       # Semi-transparent black background
        "BorderStyle=3,"               # Box background style
        "Alignment=2,"                 # Bottom center alignment
        "MarginV=40"                   # 40px margin from bottom
    )