"""
Voiceover generator: produces AI voiceover audio from script narration.
OpenAI TTS → gTTS (free) → silent WAV fallback.
"""
import io
import logging
import os
import struct
import wave
from pathlib import Path

logger = logging.getLogger(__name__)

OPENAI_TTS_AVAILABLE = False
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_TTS_AVAILABLE = True
except ImportError:
    pass

GTTS_AVAILABLE = False
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    pass


def _silent_wav(duration_seconds: float, sample_rate: int = 24000) -> bytes:
    """Generate silent WAV bytes for given duration."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        n_frames = int(duration_seconds * sample_rate)
        wav.writeframes(struct.pack(f"<{n_frames}h", *([0] * n_frames)))
    return buf.getvalue()


def generate_voiceover_openai(text: str, output_path: str | Path) -> bool:
    """Generate voiceover using OpenAI TTS and save to output_path (WAV)."""
    if not OPENAI_TTS_AVAILABLE:
        return False
    try:
        client = OpenAI()
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text[:4096],
        )
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        logger.warning("OpenAI TTS failed: %s", e)
        return False


def _generate_voiceover_gtts(text: str, output_path: Path) -> bool:
    """Generate voiceover using gTTS (free), save as MP3. FFmpeg accepts MP3."""
    if not GTTS_AVAILABLE or not text.strip():
        return False
    try:
        tts = gTTS(text=text[:5000], lang="en", slow=False)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tts.save(str(output_path))
        return True
    except Exception as e:
        logger.warning("gTTS failed: %s", e)
        return False


def generate_voiceover(
    narration: str,
    hook_text: str,
    output_path: str | Path,
    duration_seconds: float = 30.0,
) -> str | None:
    """
    Generate voiceover audio. Returns path to WAV or MP3.
    Order: OpenAI TTS → gTTS (free) → silent WAV.
    """
    full_text = f"{hook_text}. {narration}" if hook_text else (narration or "Content.")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if generate_voiceover_openai(full_text, path):
        return str(path)
    # gTTS outputs MP3; use same base path with .mp3 (FFmpeg accepts it)
    mp3_path = path.with_suffix(".mp3")
    if _generate_voiceover_gtts(full_text, mp3_path):
        logger.info("Wrote gTTS MP3 to %s", mp3_path)
        return str(mp3_path)
    # Fallback: silent WAV
    wav_bytes = _silent_wav(duration_seconds)
    with open(path, "wb") as f:
        f.write(wav_bytes)
    logger.info("Wrote silent WAV fallback to %s", path)
    return str(path)
