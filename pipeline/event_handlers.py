"""
pipeline/event_handlers.py
------------------------
Candidate speech handler — routes Deepgram transcription to the state machine.
Extracted from pipeline/pipeline_builder.py.
"""

import asyncio

from state_machine.states import InterviewState, SessionSnapshot
from state_machine.interview_flow import handle_answer_received
from subagents.evaluator_agent import spawn_evaluation
from utils.logger import get_logger

log = get_logger(__name__)


def make_on_candidate_speech(ctx: dict, snap: SessionSnapshot, speak, ws_emit):
    """Returns an async handler for Deepgram transcription events."""
    latest_score: list[float] = [0.6]

    async def on_candidate_speech(message: dict, sim_log) -> None:
        if snap.current_state != InterviewState.LISTENING:
            return
        transcript = message.get("text", "").strip()
        if not transcript:
            return

        sim_log.info("Candidate speech received", chars=len(transcript))

        # Score the answer asynchronously — result feeds the next transition
        def on_score(score: float) -> None:
            latest_score[0] = score

        spawn_evaluation(ctx, snap, transcript, ws_emit, on_score)

        # Brief delay so evaluation has a chance to start before transition
        await asyncio.sleep(0.5)
        await handle_answer_received(ctx, snap, speak, latest_score[0])

    return on_candidate_speech
