"""
pipeline/speaking_gate.py
--------------------------
Async event gate tracking whether the agent is currently playing TTS audio.

speak() calls gate.started() before queuing audio and gate.wait_done() after.
This blocks the state machine from advancing to LISTENING while the agent is
still mid-sentence — the root cause of the erratic transcript-on-agent-audio bug.
"""

import asyncio
from utils.logger import get_logger

log = get_logger(__name__)


class SpeakingGate:
    """asyncio Event wrapper — cleared while agent speaks, set when done."""

    def __init__(self):
        self._done = asyncio.Event()
        self._done.set()   # initially: not speaking

    def started(self) -> None:
        self._done.clear()

    def stopped(self) -> None:
        self._done.set()

    async def wait_done(self, timeout: float = 30.0) -> None:
        try:
            await asyncio.wait_for(self._done.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            log.warning("SpeakingGate: TTS timeout — unblocking state machine")
            self._done.set()
