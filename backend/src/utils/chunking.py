"""
Utility for chunking transcription segments into manageable pieces for LLM processing.

This module provides functions to divide long transcriptions into smaller chunks
that fit within token limits while preserving context through overlapping segments.
"""

from typing import List, Dict, Any
import logging

log = logging.getLogger("chunking")


def create_chunks_from_segments(
    segments: List[Dict[str, Any]],
    chunk_duration_seconds: int = 360,  # 6 minutes (middle of 5-7 min range)
    overlap_seconds: int = 30
) -> List[List[Dict[str, Any]]]:
    """
    Divides transcription segments into temporal chunks with optional overlap.

    This function groups Whisper segments into chunks based on their timestamps,
    ensuring that each chunk has approximately the specified duration while
    maintaining context through overlapping segments.

    Args:
        segments: List of Whisper transcription segments. Each segment should have:
                 - 'start' (float): Start time in seconds
                 - 'end' (float): End time in seconds
                 - 'text' (str): Transcribed text
        chunk_duration_seconds: Target duration for each chunk in seconds (default: 6 min)
        overlap_seconds: Overlap duration between consecutive chunks (default: 30s)

    Returns:
        List of chunks, where each chunk is a list of segments.
        Empty list if segments is empty.

    Example:
        >>> segments = [
        ...     {"start": 0.0, "end": 5.0, "text": "First segment"},
        ...     {"start": 5.0, "end": 10.0, "text": "Second segment"},
        ...     {"start": 10.0, "end": 15.0, "text": "Third segment"}
        ... ]
        >>> chunks = create_chunks_from_segments(segments, chunk_duration_seconds=10, overlap_seconds=2)
        >>> len(chunks)
        2
    """
    if not segments:
        log.warning("create_chunks_from_segments called with empty segments list")
        return []

    chunks = []
    current_chunk = []
    chunk_start_time = 0.0
    chunk_end_time = chunk_duration_seconds

    log.info(
        f"Creating chunks with duration={chunk_duration_seconds}s, overlap={overlap_seconds}s"
    )

    for segment in segments:
        segment_start = segment.get("start", 0.0)
        segment_end = segment.get("end", 0.0)

        # Add segment to current chunk if it starts before chunk end time
        if segment_start < chunk_end_time:
            current_chunk.append(segment)
        else:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk)
                log.debug(
                    f"Chunk {len(chunks)} created: {len(current_chunk)} segments, "
                    f"duration: {current_chunk[0]['start']:.1f}s - {current_chunk[-1]['end']:.1f}s"
                )

            # Calculate new chunk boundaries with overlap
            chunk_start_time = chunk_end_time - overlap_seconds
            chunk_end_time = chunk_start_time + chunk_duration_seconds

            # Start new chunk with overlapping segments
            current_chunk = []
            # Add segments from overlap period
            for prev_seg in chunks[-1] if chunks else []:
                if prev_seg.get("start", 0.0) >= chunk_start_time:
                    current_chunk.append(prev_seg)

            # Add current segment
            current_chunk.append(segment)

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)
        log.debug(
            f"Chunk {len(chunks)} (final) created: {len(current_chunk)} segments, "
            f"duration: {current_chunk[0]['start']:.1f}s - {current_chunk[-1]['end']:.1f}s"
        )

    log.info(f"Created {len(chunks)} chunks from {len(segments)} segments")
    return chunks


def get_chunk_text(chunk: List[Dict[str, Any]]) -> str:
    """
    Extracts and concatenates text from all segments in a chunk.

    Args:
        chunk: List of segment dictionaries containing 'text' field

    Returns:
        Concatenated text from all segments, space-separated
    """
    return " ".join(segment.get("text", "") for segment in chunk).strip()


def get_chunk_time_range(chunk: List[Dict[str, Any]]) -> tuple[float, float]:
    """
    Gets the time range (start, end) covered by a chunk.

    Args:
        chunk: List of segment dictionaries with 'start' and 'end' fields

    Returns:
        Tuple of (start_time, end_time) in seconds
        Returns (0.0, 0.0) if chunk is empty
    """
    if not chunk:
        return (0.0, 0.0)

    start_time = chunk[0].get("start", 0.0)
    end_time = chunk[-1].get("end", 0.0)

    return (start_time, end_time)


def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a text string.

    Uses a simple heuristic: ~4 characters per token (common for English/Portuguese).
    This is a rough estimate; actual token count depends on the tokenizer.

    Args:
        text: Input text string

    Returns:
        Estimated token count
    """
    return len(text) // 4


def should_use_chunking(transcription_text: str, threshold_chars: int = 20000) -> bool:
    """
    Determines if a transcription should be processed using chunking.

    Args:
        transcription_text: Full transcription text
        threshold_chars: Character count threshold for using chunking (default: 20000)

    Returns:
        True if transcription should be chunked, False otherwise
    """
    text_length = len(transcription_text)
    use_chunking = text_length > threshold_chars

    log.info(
        f"Transcription length: {text_length} chars, "
        f"threshold: {threshold_chars} chars, "
        f"use_chunking: {use_chunking}"
    )

    return use_chunking
