"""
Virality model inference: predicts viral probability from trend_score, hashtags, caption_length, duration, embedding.
"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_virality_model(checkpoint_path: str) -> Any:
    """Load PyTorch virality model from checkpoint. Returns None if file missing or torch unavailable."""
    if not Path(checkpoint_path).exists():
        logger.debug("No checkpoint at %s", checkpoint_path)
        return None
    try:
        import torch
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        # Stub: real implementation would rebuild nn.Module and load state_dict
        return {"state": state, "device": "cpu"}
    except Exception as e:
        logger.debug("Could not load virality model: %s", e)
        return None


def predict(
    model: Any,
    trend_score: float,
    hashtags: list[str],
    caption_length: int,
    video_duration: float,
    topic_embedding: list[float] | None = None,
) -> float:
    """
    Run virality model inference. Returns score in [0, 1].
    If model is None or dict stub, use heuristic.
    """
    if model is None or (isinstance(model, dict) and "state" in model):
        return _heuristic(trend_score, hashtags, caption_length, video_duration)
    try:
        import torch
        # Placeholder: real model would take tensor inputs
        x = torch.tensor([
            trend_score,
            len(hashtags) / 20.0,
            min(1.0, caption_length / 500.0),
            min(1.0, video_duration / 60.0),
        ], dtype=torch.float32).unsqueeze(0)
        # If model is nn.Module: model.eval(); with torch.no_grad(): out = model(x); return out.sigmoid().item()
        return _heuristic(trend_score, hashtags, caption_length, video_duration)
    except Exception as e:
        logger.warning("Virality predict failed: %s", e)
        return _heuristic(trend_score, hashtags, caption_length, video_duration)


def _heuristic(
    trend_score: float,
    hashtags: list[str],
    caption_length: int,
    video_duration: float,
) -> float:
    cap_norm = min(1.0, caption_length / 300) * 0.3
    dur_ok = 0.3 if 15 <= video_duration <= 60 else 0.1
    tag_ok = min(1.0, len(hashtags) / 10) * 0.2
    return min(1.0, trend_score * 0.4 + cap_norm + dur_ok + tag_ok)
