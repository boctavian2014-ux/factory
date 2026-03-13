"""
Stock media (Pexels) for ShortsGenerator-style scene images.
Fetches photos (and optionally videos) by keyword for video backgrounds.
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

import requests

from shared.config import settings

logger = logging.getLogger(__name__)

PEXELS_API = "https://api.pexels.com"


def _headers() -> dict:
    key = (settings.pexels_api_key or "").strip()
    if not key:
        return {}
    return {"Authorization": key}


def search_photo(query: str, orientation: str = "portrait") -> Optional[str]:
    """
    Search Pexels for one photo; download to temp file and return local path.
    Returns None if no key, no results, or on error.
    """
    if not (settings.pexels_api_key and settings.enable_stock_media):
        return None
    try:
        r = requests.get(
            f"{PEXELS_API}/v1/search",
            params={"query": query, "per_page": 1, "orientation": orientation},
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        photos = data.get("photos") or []
        if not photos:
            return None
        src = photos[0].get("src") or {}
        url = src.get("large") or src.get("original") or src.get("medium")
        if not url:
            return None
        suf = ".jpg" if ".jpg" in url.lower() else ".jpeg"
        path = Path(tempfile.gettempdir()) / f"pexels_{hash(query) % 10**8}{suf}"
        urlretrieve(url, path)
        return str(path)
    except Exception as e:
        logger.warning("Pexels search_photo failed for %s: %s", query, e)
        return None


def get_background_image_for_script(concept: str, hook: str = "") -> Optional[str]:
    """
    Get one background image for a script (concept + hook keywords).
    Used when enable_stock_media is True for native video render.
    """
    query = f"{concept} {hook}".strip() or "content creation"
    return search_photo(query, orientation="portrait")
