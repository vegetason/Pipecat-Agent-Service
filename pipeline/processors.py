"""
pipeline/processors.py
----------------------
Creates the STT (Deepgram) and TTS (Cartesia) processor instances.
"""

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService, DeepgramSTTSettings

from config import config
from utils.logger import get_logger

log = get_logger(__name__)


def create_stt(simulation_id: str) -> DeepgramSTTService:
    log.info("Creating Deepgram STT processor", simulation_id=simulation_id)
    return DeepgramSTTService(
        api_key=config.deepgram.api_key,
        settings=DeepgramSTTSettings(
            model=config.deepgram.model,
            language=config.deepgram.language,
            smart_format=True,
            endpointing=config.deepgram.endpointing_ms,
            interim_results=True,
            utterance_end_ms=1500,
        ),
    )


def create_tts(simulation_id: str) -> CartesiaTTSService:
    log.info("Creating Cartesia TTS processor", simulation_id=simulation_id)
    return CartesiaTTSService(
        api_key=config.cartesia.api_key,
        voice_id=config.cartesia.default_voice_id or None,
        model=config.cartesia.model,
    )


def create_vad(simulation_id: str) -> SileroVADAnalyzer:
    log.info("Creating VAD analyzer", simulation_id=simulation_id)
    return SileroVADAnalyzer()
