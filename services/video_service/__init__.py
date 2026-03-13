"""Video service: renders vertical short-form videos from scripts (voiceover + subtitles + FFmpeg)."""
from .main import router
from .video_renderer import render_video
from .voiceover_generator import generate_voiceover
from .subtitle_generator import generate_srt

__all__ = ["router", "render_video", "generate_voiceover", "generate_srt"]
