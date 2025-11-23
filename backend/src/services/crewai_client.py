import os
import json
import logging
from typing import Dict, Any

import requests

log = logging.getLogger("crewai_client")

# Config via env
CREWAI_ENABLED = os.getenv("CREWAI_ENABLED", "false").lower() == "true"
CREWAI_API_URL = os.getenv("CREWAI_API_URL", "")
CREWAI_API_KEY = os.getenv("CREWAI_API_KEY", "")
CREWAI_TIMEOUT = float(os.getenv("CREWAI_TIMEOUT_SECONDS", "5"))
CREWAI_MIN_HIGHLIGHT_SECONDS = float(os.getenv("CREWAI_MIN_HIGHLIGHT_SECONDS", "5"))


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if CREWAI_API_KEY:
        headers["Authorization"] = f"Bearer {CREWAI_API_KEY}"
    return headers


def plan_job(state: Dict[str, Any]) -> Dict[str, Any]:
    """Request a plan from CrewAI.

    If CrewAI is disabled or unreachable, returns a safe fallback plan (may be empty).
    The returned dict should contain keys: `highlights` (list) and `editor_params` (dict).
    """

    # If disabled or no URL configured, return fallback using existing analyst output
    if not CREWAI_ENABLED or not CREWAI_API_URL:
        log.info("CrewAI disabled or not configured — returning fallback plan.")
        # Try to reuse analyst output if available
        existing = state.get("highlight") or state.get("highlights")
        if isinstance(existing, dict) and "highlights" in existing:
            return {"highlights": existing.get("highlights", []), "editor_params": {}}
        return {"highlights": [], "editor_params": {}}

    payload = {
        "transcription": state.get("transcription", {}),
        "metadata": {
            "url": state.get("url"),
            "video_path": state.get("video_path"),
        },
    }

    try:
        resp = requests.post(
            f"{CREWAI_API_URL.rstrip('/')}/plan",
            json=payload,
            headers=_headers(),
            timeout=CREWAI_TIMEOUT,
        )
        resp.raise_for_status()
        plan = resp.json()
        # Coerce structure
        if not isinstance(plan, dict):
            log.warning("CrewAI returned non-dict plan; using fallback")
            return {"highlights": [], "editor_params": {}}
        return plan
    except Exception as exc:  # network, timeout, JSON decode, etc.
        log.exception(f"CrewAI plan_job failed: {exc}")
        # Fallback: reuse existing highlights if present
        existing = state.get("highlight") or state.get("highlights")
        if isinstance(existing, dict) and "highlights" in existing:
            return {"highlights": existing.get("highlights", []), "editor_params": {}}
        return {"highlights": [], "editor_params": {}}


def summarize(text: str, max_chars: int = 512) -> str:
    """Simple wrapper for summarization — stub uses naive truncate when CrewAI disabled."""
    if not CREWAI_ENABLED or not CREWAI_API_URL:
        return (text or "")[:max_chars]

    try:
        resp = requests.post(
            f"{CREWAI_API_URL.rstrip('/')}/summarize",
            json={"text": text, "max_chars": max_chars},
            headers=_headers(),
            timeout=CREWAI_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("summary") or (text or "")[:max_chars]
    except Exception:
        log.exception("CrewAI summarize failed, falling back to truncate")
        return (text or "")[:max_chars]


def extract_highlights(text: str, max_items: int = 5) -> list:
    """Extract candidate highlights from text — stub behavior when disabled.

    Returns a list of dicts with start,end,summary,score keys when possible.
    """
    if not CREWAI_ENABLED or not CREWAI_API_URL:
        # Fallback stub: return empty list — analyst/local heuristics should handle
        return []

    try:
        resp = requests.post(
            f"{CREWAI_API_URL.rstrip('/')}/extract_highlights",
            json={"text": text, "max_items": max_items},
            headers=_headers(),
            timeout=CREWAI_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("highlights", [])
    except Exception:
        log.exception("CrewAI extract_highlights failed")
        return []
