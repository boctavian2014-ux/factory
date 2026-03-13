"""
Client for external text-to-video APIs (Open-Sora server, Sora-2-Generator style).
Prompt → POST to API → download video file.
"""
import logging
import uuid
from pathlib import Path
from urllib.request import urlretrieve

import requests

from shared.config import settings

logger = logging.getLogger(__name__)


def generate_video_via_api(
    prompt: str,
    duration_seconds: float = 15.0,
    output_dir: str | Path | None = None,
) -> str | None:
    """
    Call external video generation API with prompt; download result to output_dir.
    Expects API to accept POST with JSON { "prompt": "...", "duration_seconds": N }
    and return JSON { "video_url": "..." } or { "output_path": "..." } or similar.
    Returns path to downloaded video file or None on failure.
    """
    url = (settings.video_api_url or "").strip()
    if not url:
        logger.warning("VIDEO_API_URL not set; cannot use external video API")
        return None
    out_dir = Path(output_dir or settings.videos_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"api_{uuid.uuid4().hex[:12]}.mp4"

    try:
        payload = {"prompt": prompt, "duration_seconds": duration_seconds}
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        video_url = data.get("video_url") or data.get("url") or data.get("output_url")
        if not video_url:
            # Some APIs return binary MP4 directly
            if r.content and len(r.content) > 100:
                out_path.write_bytes(r.content)
                return str(out_path)
            logger.warning("External API response had no video_url or binary body")
            return None
        urlretrieve(video_url, out_path)
        return str(out_path)
    except Exception as e:
        logger.warning("External video API failed: %s", e)
        return None
