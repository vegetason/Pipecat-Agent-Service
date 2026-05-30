"""
pipeline/event_handlers.py
------------------------
Candidate speech handler — routes Deepgram transcription to the state machine.
Extracted from pipeline/pipeline_builder.py.

FIX: Replaced the 0.5s asyncio.sleep() race condition with a proper
asyncio.Event(). The old code read latest_score[0] after only 500ms,
which is rarely enough for a Groq evaluation call to complete. The result
was that the state machine almost always used the default fallback score
of 0.6 (triggering a follow-up) rather than the real score (which might
trigger escalation or transition). Now we wait up to 3 seconds for the
real score, then fall back cleanly if Groq is slow.
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

        # Use an Event so we block until the real score arrives, rather than
        # sleeping a fixed 500ms and almost always reading the default 0.6.
        score_ready = asyncio.Event()

        def on_score(score: float) -> None:
            latest_score[0] = score
            score_ready.set()

        # Capture index NOW — snapshot.current_question_index may change before
        # the evaluation task runs (handle_transitioning increments it).
        captured_index = snap.current_question_index
        spawn_evaluation(ctx, snap, transcript, ws_emit, on_score, captured_index)

        # Wait up to 3s for Groq to return a real score.
        # If it times out we fall back to the default 0.6, which is the same
        # safe value as before — just now it's an intentional fallback, not
        # a guaranteed race condition loss.
        try:
            await asyncio.wait_for(score_ready.wait(), timeout=3.0)
            sim_log.debug("Evaluation score received", score=latest_score[0])
        except asyncio.TimeoutError:
            sim_log.warning(
                "Evaluation timed out after 3s — using default score",
                default_score=latest_score[0],
            )

        await handle_answer_received(ctx, snap, speak, latest_score[0])

    return on_candidate_speech