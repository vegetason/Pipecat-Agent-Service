"""
pipeline/processors.py
-----------------------
Creates the STT (Deepgram) and TTS (Cartesia) processor instances.
These are Pipecat frame processors that sit inside the pipeline.
Imported by pipeline_builder.py only.
"""

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transcriptions.language import Language

from config import config
from utils.logger import get_logger

log = get_logger(__name__)


def create_stt(simulation_id: str) -> DeepgramSTTService:
    """
    Create the Deepgram Speech-to-Text processor.
    VAD (Voice Activity Detection) is attached so the pipeline knows
    when the candidate starts and stops speaking.
    """
    log.info("Creating Deepgram STT processor", simulation_id=simulation_id)
    return DeepgramSTTService(
        api_key=config.deepgram.api_key,
        live_options={
            "model": config.deepgram.model,
            "language": config.deepgram.language,
            "smart_format": True,
            "endpointing": config.deepgram.endpointing_ms,
            "vad_events": True,
            "utterance_end_ms": 1500,
        },
    )


def create_tts(simulation_id: str) -> CartesiaTTSService:
    """
    Create the Cartesia Text-to-Speech processor.
    Voice ID can be overridden per persona — default used here,
    pipeline_builder swaps it per persona if needed.
    """
    log.info("Creating Cartesia TTS processor", simulation_id=simulation_id)
    return CartesiaTTSService(
        api_key=config.cartesia.api_key,
        voice_id=config.cartesia.default_voice_id,
        model=config.cartesia.model,
    )


def create_vad(simulation_id: str) -> SileroVADAnalyzer:
    """
    Create the Voice Activity Detector.
    Tells the pipeline when audio contains speech vs silence.
    Used to trigger silence timeout logic in the state machine.
    """
    log.info("Creating VAD analyzer", simulation_id=simulation_id)
    return SileroVADAnalyzer()
