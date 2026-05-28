"""
pipeline/transport.py
----------------------
Creates and configures the Daily.co WebRTC transport.
Daily is what puts the agent inside the video room with the candidate.
Imported by pipeline_builder.py only.
"""

from daily import EventHandler
from pipecat.transports.services.daily import DailyTransport, DailyParams
from config import config
from utils.logger import get_logger

log = get_logger(__name__)


def create_transport(room_url: str, simulation_id: str) -> DailyTransport:
    """
    Create a Daily.co transport for a simulation session.

    Args:
        room_url:      The Daily room URL from the simulation context.
        simulation_id: Used for logging and the bot's display name in the room.
    """
    log.info("Creating Daily transport", simulation_id=simulation_id, room_url=room_url)

    params = DailyParams(
        audio_in_enabled=True,     # Receive candidate's microphone audio
        audio_out_enabled=True,    # Send agent's TTS audio back
        camera_out_enabled=False,  # Agent has no video feed
        transcription_enabled=False,  # We use Deepgram STT, not Daily's built-in
    )

    transport = DailyTransport(
        room_url=room_url,
        token=None,                 # Public room — no token required
        bot_name=f"Interviewer",
        params=params,
        api_key=config.daily.api_key,
    )

    log.info("Daily transport created", simulation_id=simulation_id)
    return transport