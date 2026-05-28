"""
services/voice_cloning.py
------------------------
ElevenLabs Voice Lab integration for Ghost Mode.
Creates voice clones from user audio samples and synthesizes TTS
using the cloned voice.
"""

from elevenlabs import ElevenLabs
from config import config
from utils.logger import get_logger

log = get_logger(__name__)
_client = ElevenLabs(api_key=config.elevenlabs.api_key)


async def create_voice_clone(name: str, audio_files: list[str], description: str = "") -> str | None:
    """Upload audio samples and create a voice clone. Returns the voice_id."""
    if len(audio_files) < 1:
        log.error("Voice clone requires audio samples")
        return None
    try:
        voice = _client.clone(
            name=name,
            files=audio_files,
            description=description or f"Ghost Mode clone for {name}",
        )
        log.info("Voice clone created", voice_id=voice.voice_id, name=name)
        return voice.voice_id
    except Exception as e:
        log.error("Voice clone creation failed", error=str(e))
        return None


async def synthesize_with_clone(voice_id: str, text: str) -> bytes | None:
    """Synthesize text into audio using a cloned voice. Returns raw audio bytes."""
    try:
        audio = _client.generate(text=text, voice=voice_id, model=config.elevenlabs.model)
        return b"".join(audio)
    except Exception as e:
        log.error("Clone synthesis failed", voice_id=voice_id, error=str(e))
        return None


async def synthesize_ideal_answers(voice_id: str, answers: list[str]) -> list[bytes]:
    """Batch-synthesize Ghost Mode ideal answers with cloned voice."""
    results: list[bytes] = []
    for i, answer in enumerate(answers):
        audio = await synthesize_with_clone(voice_id, answer)
        if audio:
            results.append(audio)
            log.info("Ghost answer synthesized", index=i, bytes=len(audio))
    return results
