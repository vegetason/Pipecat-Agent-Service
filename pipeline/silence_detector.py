"""
pipeline/silence_detector.py
----------------------------
Pipecat frame processor — detects extended candidate silence during LISTENING.

On UserStoppedSpeakingFrame: starts a countdown timer.
On UserStartedSpeakingFrame: cancels it.
On timeout: calls handle_silence_detected() on the state machine.
"""

import asyncio
from typing import Callable, Awaitable

from pipecat.frames.frames import UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameProcessor

from config import config
from state_machine.states import InterviewState, SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)

SpeakFn = Callable[[str], Awaitable[None]]


class SilenceDetector(FrameProcessor):
    """
    Passthrough processor on the audio path.
    Listens for VAD boundary frames; manages a configurable silence timer.
    Only fires when the state machine is in LISTENING state.
    """

    def __init__(self, ctx: dict, snap: SessionSnapshot, speak: SpeakFn):
        super().__init__()
        self._ctx = ctx
        self._snap = snap
        self._speak = speak
        self._timer: asyncio.Task | None = None
        self._sim_id = ctx["simulation_id"]
        self._log = log.bind(simulation_id=self._sim_id)

    async def process_frame(self, frame, direction):
        # CRITICAL: call super() first so base class handles StartFrame/CancelFrame.
        await super().process_frame(frame, direction)

        # Always pass every frame through unchanged.
        await self.push_frame(frame, direction)

        if isinstance(frame, UserStoppedSpeakingFrame):
            if self._snap.current_state == InterviewState.LISTENING:
                self._start_timer()

        elif isinstance(frame, UserStartedSpeakingFrame):
            self._cancel_timer()

    def _start_timer(self) -> None:
        self._cancel_timer()
        self._timer = asyncio.create_task(self._run_timeout())

    def _cancel_timer(self) -> None:
        if self._timer and not self._timer.done():
            self._timer.cancel()
        self._timer = None

    async def _run_timeout(self) -> None:
        """Wait for silence timeout then delegate to interview_flow handler."""
        await asyncio.sleep(config.simulation.silence_timeout_seconds)
        self._log.info("Silence timeout — notifying state machine")
        try:
            from state_machine.interview_flow import handle_silence_detected
            await handle_silence_detected(self._ctx, self._snap, self._speak)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._log.error("Silence handler failed", error=str(e))