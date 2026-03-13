"""
Virality model loader: loads PyTorch model for virality score prediction.
Delegates to ml/virality_model/predict.py when available.
"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_model(model_path: str | Path | None = None) -> Any:
    """Load virality PyTorch model. Returns None if not found or PyTorch unavailable."""
    try:
        from ml.virality_model.predict import load_virality_model
        path = model_path or Path(__file__).resolve().parents[2] / "ml" / "virality_model" / "checkpoint.pt"
        return load_virality_model(str(path))
    except Exception as e:
        logger.debug("Virality model not loaded: %s", e)
        return None


def predict_virality(
    trend_score: float,
    hashtags: list[str],
    caption_length: int,
    video_duration: float,
    topic_embedding: list[float] | None = None,
    model=None,
) -> float:
    """
    Predict virality score in [0, 1]. Uses ML model if available else heuristic.
    """
    if model is not None:
        try:
            from ml.virality_model.predict import predict
            return float(predict(model, trend_score, hashtags, caption_length, video_duration, topic_embedding))
        except Exception as e:
            logger.warning("Model prediction failed, using heuristic: %s", e)
    return _heuristic_score(trend_score, hashtags, caption_length, video_duration)


def _heuristic_score(
    trend_score: float,
    hashtags: list[str],
    caption_length: int,
    video_duration: float,
) -> float:
    """Fallback score when model is not available."""
    # Optimal caption length ~100-300 chars; duration 15-60s
    cap_norm = min(1.0, caption_length / 300) * 0.3
    dur_ok = 0.3 if 15 <= video_duration <= 60 else 0.1
    tag_ok = min(1.0, len(hashtags) / 10) * 0.2
    return min(1.0, trend_score * 0.4 + cap_norm + dur_ok + tag_ok)
