"""
Exporter: writes scheduled posts to CSV for posting tools.
"""
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CSV_HEADERS = ["video_file", "caption", "hashtags", "platform", "scheduled_time"]


def export_to_csv(rows: list[dict[str, Any]], output_path: str | Path) -> str:
    """
    Export schedule rows to CSV. Each row: video_file, caption, hashtags, platform, scheduled_time.
    hashtags written as space-separated or quoted.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = {
                "video_file": r.get("video_file", ""),
                "caption": (r.get("caption") or "").replace("\n", " "),
                "hashtags": " ".join(r.get("hashtags") or []),
                "platform": r.get("platform", ""),
                "scheduled_time": r.get("scheduled_time", ""),
            }
            if isinstance(out["scheduled_time"], datetime):
                out["scheduled_time"] = out["scheduled_time"].isoformat()
            w.writerow(out)
    return str(path)
