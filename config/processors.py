"""
config/processors.py
--------------------
Config for the three real-time processors that run inside the Pipecat pipeline:
emotion analyzer, rambling detector, and pressure multiplier.
All thresholds here are tunable via env vars without redeploying.
"""

from dataclasses import dataclass, field
from config.helpers import optional, optional_int, optional_float


@dataclass
class EmotionConfig:
    # "silero" (faster, lighter) or "wav2vec2" (more accurate, heavier)
    model_backend: str = field(
        default_factory=lambda: optional("EMOTION_MODEL_BACKEND", "silero")
    )
    # How often emotion is sampled — lower = more responsive but more CPU
    sample_interval_seconds: float = field(
        default_factory=lambda: optional_float("EMOTION_SAMPLE_INTERVAL", 2.0)
    )
    high_stress_threshold: float = field(
        default_factory=lambda: optional_float("EMOTION_HIGH_STRESS_THRESHOLD", 0.7)
    )
    calm_threshold: float = field(
        default_factory=lambda: optional_float("EMOTION_CALM_THRESHOLD", 0.3)
    )


@dataclass
class RamblingConfig:
    # Token count at which we start checking for rambling
    token_count_threshold: int = field(
        default_factory=lambda: optional_int("RAMBLING_TOKEN_THRESHOLD", 150)
    )
    # Cosine similarity above this = semantic repetition detected
    similarity_threshold: float = field(
        default_factory=lambda: optional_float("RAMBLING_SIMILARITY_THRESHOLD", 0.85)
    )
    # Sliding window size (in sentences) for similarity comparison
    window_size: int = field(
        default_factory=lambda: optional_int("RAMBLING_WINDOW_SIZE", 3)
    )


@dataclass
class PressureConfig:
    # Answer score above this triggers an escalation challenge
    escalation_trigger_score: float = field(
        default_factory=lambda: optional_float("PRESSURE_ESCALATION_SCORE", 0.85)
    )
    max_escalations: int = field(
        default_factory=lambda: optional_int("PRESSURE_MAX_ESCALATIONS", 3)
    )