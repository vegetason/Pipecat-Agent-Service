"""
config/__init__.py
------------------
Assembles all config sections into one Config object.
Every file in the codebase imports like this:

    from config import config
    config.claude.api_key
    config.emotion.high_stress_threshold
"""

from dataclasses import dataclass, field
from config.helpers import optional

from config.server import ServerConfig, NodeAPIConfig
from config.providers import (
    DailyConfig,
    DeepgramConfig,
    ClaudeConfig,
    CartesiaConfig,
    ElevenLabsConfig,
)
from config.processors import EmotionConfig, RamblingConfig, PressureConfig
from config.simulation import SimulationConfig, FeatureFlags


@dataclass
class Config:
    server: ServerConfig = field(default_factory=ServerConfig)
    node_api: NodeAPIConfig = field(default_factory=NodeAPIConfig)
    daily: DailyConfig = field(default_factory=DailyConfig)
    deepgram: DeepgramConfig = field(default_factory=DeepgramConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    cartesia: CartesiaConfig = field(default_factory=CartesiaConfig)
    elevenlabs: ElevenLabsConfig = field(default_factory=ElevenLabsConfig)
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    rambling: RamblingConfig = field(default_factory=RamblingConfig)
    pressure: PressureConfig = field(default_factory=PressureConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    env: str = field(default_factory=lambda: optional("APP_ENV", "development"))

    @property
    def is_dev(self) -> bool:
        return self.env == "development"

    @property
    def is_prod(self) -> bool:
        return self.env == "production"


# Single shared instance — import this everywhere
config = Config()