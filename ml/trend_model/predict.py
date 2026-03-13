"""
Trend model inference: optional scoring/embedding for trends.
Used by trend-service if needed; stub for production training pipeline.
"""
from typing import Any


def load_trend_model(checkpoint_path: str) -> Any:
    """Load trend model from checkpoint. Stub returns None."""
    return None


def predict_trend_score(signals: dict[str, Any]) -> float:
    """Predict trend score from raw signals. Stub returns 0.5."""
    return 0.5
