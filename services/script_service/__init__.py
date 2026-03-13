"""Script service: converts ideas into scripts with scene breakdown and overlays."""
from .main import router
from .script_generator import generate_script
from .scene_generator import scenes_from_narration, text_overlays_from_scenes

__all__ = ["router", "generate_script", "scenes_from_narration", "text_overlays_from_scenes"]
