"""Virality service: ML-based virality scoring for videos."""
from .main import router
from .virality_model import load_model, predict_virality

__all__ = ["router", "load_model", "predict_virality"]
