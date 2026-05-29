"""
processors/rambling_detector.py
--------------------------------
Pipecat frame processor — watches the live transcript and fires an interrupt
when the candidate is rambling. Calls on_interrupt() on detection.
"""

from typing import Callable, Awaitable

from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.frame_processor import FrameProcessor

from processors.rambling_scorer import is_rambling
from state_machine.states import InterviewState, SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)

InterruptCallback = Callable[[str], Awaitable[None]]


class RamblingDetector(FrameProcessor):
    """
    Passthrough processor on the transcript path.
    Accumulates candidate speech per question, scores for rambling,
    and interrupts when threshold is crossed.
    """

    def __init__(
        self,
        simulation_id: str,
        snapshot: SessionSnapshot,
        on_interrupt: InterruptCallback,
    ):
        super().__init__()
        self._sim_id = simulation_id
        self._snapshot = snapshot
        self._on_interrupt = on_interrupt
        self._full_text = ""
        self._sentences: list[str] = []
        self._interrupted = False
        self._last_q_index: int = 0
        self._log = log.bind(simulation_id=simulation_id)

    def reset_for_new_question(self) -> None:
        """Call this every time the state machine transitions to a new question."""
        self._full_text = ""
        self._sentences = []
        self._interrupted = False

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)

        # Auto-reset when question index advances — prevents carry-over between questions.
        current_q = self._snapshot.current_question_index
        if current_q != self._last_q_index:
            self.reset_for_new_question()
            self._last_q_index = current_q

        # Only inspect transcription frames while candidate is speaking.
        if not isinstance(frame, TranscriptionFrame):
            return
        if self._snapshot.current_state != InterviewState.LISTENING:
            return
        if self._interrupted:
            return

        text = frame.text.strip()
        if not text:
            return

        self._full_text += " " + text
        self._sentences.append(text)
        self._log.debug("Transcript chunk", tokens=len(self._full_text) // 4)

        if is_rambling(self._full_text, self._sentences):
            await self._interrupt()

    async def _interrupt(self) -> None:
        self._interrupted = True
        self._log.info("Rambling detected — interrupting candidate")
        await self._on_interrupt(self._sim_id)


def make_interrupt_callback(speak) -> InterruptCallback:
    """
    Returns the callback fired when rambling is detected.
    Makes the agent deliver a polite cut-off via the speak function.
    """
    async def on_interrupt(sim_id: str) -> None:
        await speak(
            "Interrupt the candidate politely but firmly. "
            "Say: 'Let me stop you there — can you give me the one-sentence "
            "version of your answer?'"
        )
    return on_interrupt