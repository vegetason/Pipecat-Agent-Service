"""
config/providers.py
-------------------
Config for every external API provider the agent communicates with.
"""

from dataclasses import dataclass, field
from config.helpers import require, optional, optional_int, optional_float


@dataclass
class LiveKitConfig:
    url: str = field(default_factory=lambda: optional("LIVEKIT_URL", ""))
    api_key: str = field(default_factory=lambda: optional("LIVEKIT_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: optional("LIVEKIT_API_SECRET", ""))
    bot_identity: str = field(default_factory=lambda: optional("LIVEKIT_BOT_IDENTITY", "interviewer"))


@dataclass
class DeepgramConfig:
    api_key: str = field(default_factory=lambda: require("DEEPGRAM_API_KEY"))
    model: str = field(default_factory=lambda: optional("DEEPGRAM_MODEL", "nova-2"))
    language: str = field(default_factory=lambda: optional("DEEPGRAM_LANGUAGE", "en-US"))
    # Stop sending audio to LLM after this many ms of silence
    endpointing_ms: int = field(
        default_factory=lambda: optional_int("DEEPGRAM_ENDPOINTING_MS", 500)
    )


@dataclass
class GroqConfig:
    api_key: str = field(default_factory=lambda: require("GROQ_API_KEY"))
    model: str = field(
        default_factory=lambda: optional("GROQ_MODEL", "llama-3.1-8b-instant")
    )
    # Short for natural interviewer responses
    max_tokens: int = field(default_factory=lambda: optional_int("GROQ_MAX_TOKENS", 300))
    # Longer for Ghost Mode ideal answer generation
    ghost_mode_max_tokens: int = field(
        default_factory=lambda: optional_int("GROQ_GHOST_MAX_TOKENS", 800)
    )
    temperature: float = field(
        default_factory=lambda: optional_float("GROQ_TEMPERATURE", 0.7)
    )


@dataclass
class CartesiaConfig:
    api_key: str = field(default_factory=lambda: require("CARTESIA_API_KEY"))
    model: str = field(
        default_factory=lambda: optional("CARTESIA_MODEL", "sonic-english")
    )
    default_voice_id: str = field(
        default_factory=lambda: optional("CARTESIA_DEFAULT_VOICE_ID", "")
    )


@dataclass
class ElevenLabsConfig:
    api_key: str = field(default_factory=lambda: require("ELEVENLABS_API_KEY"))
    model: str = field(
        default_factory=lambda: optional("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    )
    # Minimum audio seconds required before attempting a voice clone
    min_clone_audio_seconds: int = field(
        default_factory=lambda: optional_int("ELEVENLABS_MIN_CLONE_SECONDS", 30)
    )
