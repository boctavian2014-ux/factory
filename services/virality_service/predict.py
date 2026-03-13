"""
Virality prediction: thin wrapper for ml.virality_model.predict.
"""
from .virality_model import load_model, predict_virality

__all__ = ["load_model", "predict_virality"]
