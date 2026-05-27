"""
config/simulation.py
--------------------
Simulation runtime defaults and feature flags.
"""

from dataclasses import dataclass, field
from config.helpers import optional_int, optional_bool


@dataclass
class SimulationConfig:
    waiting_room_min_seconds: int = field(
        default_factory=lambda: optional_int("WAITING_ROOM_MIN_SECONDS", 60)
    )
    waiting_room_max_seconds: int = field(
        default_factory=lambda: optional_int("WAITING_ROOM_MAX_SECONDS", 90)
    )
    max_followups_per_question: int = field(
        default_factory=lambda: optional_int("MAX_FOLLOWUPS_PER_QUESTION", 2)
    )
    # Seconds of silence before agent gives one neutral prompt
    silence_timeout_seconds: int = field(
        default_factory=lambda: optional_int("SILENCE_TIMEOUT_SECONDS", 8)
    )
    # Seconds of silence after neutral prompt before agent moves on
    silence_move_on_seconds: int = field(
        default_factory=lambda: optional_int("SILENCE_MOVE_ON_SECONDS", 5)
    )


@dataclass
class FeatureFlags:
    # Requires ElevenLabs + explicit user consent stored in DB
    ghost_mode_enabled: bool = field(
        default_factory=lambda: optional_bool("FEATURE_GHOST_MODE", True)
    )
    # Show live stress indicator on candidate's screen during simulation
    live_emotion_display: bool = field(
        default_factory=lambda: optional_bool("FEATURE_LIVE_EMOTION_DISPLAY", True)
    )
    # Score answers in parallel while simulation is running
    live_evaluation_enabled: bool = field(
        default_factory=lambda: optional_bool("FEATURE_LIVE_EVALUATION", True)
    )