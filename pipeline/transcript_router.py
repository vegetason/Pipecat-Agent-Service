"""
pipeline/transcript_router.py
------------------------------
Pipecat frame processor — intercepts TranscriptionFrame from Deepgram STT
and routes it to the state machine and WebSocket logger.

FIX 1: The original code used @stt.event_handler("on_transcription_message")
which is a non-existent event name in pipecat 1.3. Transcriptions are not
emitted as events — they flow as TranscriptionFrame objects through the
pipeline. This processor catches them reliably as a passthrough.

FIX 2: Added SpeakingGate guard — Deepgram picks up the agent's own TTS
audio and transcribes it, causing the state machine to treat agent speech
as candidate speech and jump to the next question. The gate blocks all
transcription frames while the agent is speaking.
"""

import asyncio
from typing import Callable, Awaitable

from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.frame_processor import FrameProcessor

from pipeline.speaking_gate import SpeakingGate
from state_machine.states import SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)
WsEmit = Callable[[str, dict], Awaitable[None]]


class TranscriptRouter(FrameProcessor):
    """
    Passthrough processor. Catches TranscriptionFrame → routes to state machine.
    All frames pass through unchanged so the rest of the pipeline runs normally.

    Gate behaviour: if a SpeakingGate is provided, any transcription frame
    that arrives while the agent is speaking (gate not done) is silently
    dropped. This prevents Deepgram from transcribing TTS audio back into
    the candidate speech handler.
    """

    def __init__(
        self,
        sim_id: str,
        snap: SessionSnapshot,
        on_speech: Callable,
        ws_emit: WsEmit,
        gate: SpeakingGate | None = None,
    ):
        super().__init__()
        self._sim_id = sim_id
        self._snap = snap
        self._on_speech = on_speech
        self._ws_emit = ws_emit
        self._gate = gate
        self._log = log.bind(simulation_id=sim_id)

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)

        if not isinstance(frame, TranscriptionFrame):
            return

        text = (frame.text or "").strip()
        if not text:
            return

        # KEY FIX: drop transcription frames while the agent is speaking.
        # Without this, Deepgram transcribes TTS audio and the state machine
        # treats it as a candidate answer, jumping to the next question
        # before the candidate has said anything.
        if self._gate and not self._gate._done.is_set():
            self._log.debug("Transcript dropped — agent is speaking", chars=len(text))
            return

        self._log.debug("Transcript received", chars=len(text))
        try:
            await self._ws_emit(
                "transcript_chunk",
                {"simulation_id": self._sim_id, "text": text},
            )
            await self._on_speech({"text": text}, self._log)
        except Exception as e:
            self._log.error("Transcript routing failed", error=str(e))