"""
pipeline/transcript_router.py
------------------------------
Pipecat frame processor — intercepts TranscriptionFrame from Deepgram STT
and routes it to the state machine and WebSocket logger.

FIX: The original code used @stt.event_handler("on_transcription_message")
which is a non-existent event name in pipecat 1.3. Transcriptions are not
emitted as events — they flow as TranscriptionFrame objects through the
pipeline. This processor catches them reliably as a passthrough.
"""

import asyncio
from typing import Callable, Awaitable

from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.frame_processor import FrameProcessor

from state_machine.states import SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)
WsEmit = Callable[[str, dict], Awaitable[None]]


class TranscriptRouter(FrameProcessor):
    """
    Passthrough processor. Catches TranscriptionFrame → routes to state machine.
    All frames pass through unchanged so the rest of the pipeline runs normally.
    """

    def __init__(self, sim_id: str, snap: SessionSnapshot, on_speech, ws_emit: WsEmit):
        super().__init__()
        self._sim_id = sim_id
        self._snap = snap
        self._on_speech = on_speech
        self._ws_emit = ws_emit
        self._log = log.bind(simulation_id=sim_id)

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)

        if not isinstance(frame, TranscriptionFrame):
            return
        text = (frame.text or "").strip()
        if not text:
            return

        self._log.debug("Transcript received", chars=len(text))
        try:
            await self._ws_emit("transcript_chunk", {"simulation_id": self._sim_id, "text": text})
            await self._on_speech({"text": text}, self._log)
        except Exception as e:
            self._log.error("Transcript routing failed", error=str(e))
