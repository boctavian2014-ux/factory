"""Idea service: generates viral video ideas from trends."""
from .main import router
from .idea_generator import generate_ideas_for_trend, VideoIdea
from .hook_generator import generate_hook

__all__ = ["router", "generate_ideas_for_trend", "VideoIdea", "generate_hook"]
