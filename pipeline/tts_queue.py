"""
pipeline/tts_queue.py
--------------------
Drain loop that pulls text from the TTS queue and feeds it to Cartesia.
Extracted from pipeline/pipeline_builder.py.
"""

import asyncio

from state_machine.states import InterviewState, SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)


async def drain_tts_queue(tts_queue: asyncio.Queue, tts, snap: SessionSnapshot) -> None:
    """Continuously drain the TTS queue until the interview completes."""
    while snap.current_state != InterviewState.COMPLETED:
        try:
            text = await asyncio.wait_for(tts_queue.get(), timeout=1.0)
            await tts.say(text)
        except asyncio.TimeoutError:
            continue
