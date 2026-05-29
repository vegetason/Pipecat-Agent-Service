"""
state_machine/interview_flow.py
--------------------------------
Main interview loop. Drives the simulation from INITIALIZING to COMPLETED.
Imports all handlers from handlers.py and transition logic from transitions.py.
Called by pipeline_builder.py.
"""

import asyncio
from typing import Callable, Awaitable

from state_machine.states import InterviewState, SessionSnapshot
from state_machine.transitions import next_state_after_listening
from state_machine.handlers import (
    handle_waiting_room, handle_intro, handle_questioning, handle_silence, handle_wrap_up,
)
from state_machine.challenge_handlers import (
    handle_challenging, handle_follow_up, handle_escalating, handle_transitioning,
)
from utils.logger import get_logger

log = get_logger(__name__)

SpeakFn = Callable[[str], Awaitable[None]]
StateCb = Callable[[InterviewState], Awaitable[None]]


async def run_interview(
    ctx: dict,
    speak: SpeakFn,
    snap: SessionSnapshot,           # FIX: accept shared snap from pipeline_builder
    on_state_change: StateCb | None = None,
) -> None:
    """
    Drive the full interview from start to finish.

    Args:
        ctx:             Full simulation context dict.
        speak:           Async fn — wired to Claude + TTS by pipeline_builder.
        snap:            Shared SessionSnapshot — MUST be the same object passed to
                         make_on_candidate_speech so state changes are visible to both.
        on_state_change: Optional callback fired on every state change.
    """
    # FIX: removed internal `snap = SessionSnapshot(simulation_id=sim_id)` creation.
    # Previously, run_interview had its own private snap that was never updated by
    # handle_answer_received (which received pipeline_builder's snap). The while loop
    # checked its own snap.current_state which never reached COMPLETED — infinite loop.
    sim_id = ctx["simulation_id"]
    total  = len(ctx.get("question_bank", []))
    sim_log = log.bind(simulation_id=sim_id)

    async def go(state: InterviewState) -> None:
        snap.current_state = state
        sim_log.info("State changed", state=state.name)
        if on_state_change:
            await on_state_change(state)

    await go(InterviewState.WAITING_ROOM)
    await handle_waiting_room(snap, speak)

    await go(InterviewState.INTRO)
    await handle_intro(ctx, snap, speak)

    while snap.current_state != InterviewState.COMPLETED:
        state = snap.current_state

        if state == InterviewState.QUESTIONING:
            await handle_questioning(ctx, snap, speak)
        elif state == InterviewState.LISTENING:
            await asyncio.sleep(0.1)   # pipeline drives us out via handle_answer_received
        elif state == InterviewState.CHALLENGING:
            await handle_challenging(ctx, snap, speak)
        elif state == InterviewState.FOLLOW_UP:
            await handle_follow_up(ctx, snap, speak)
        elif state == InterviewState.ESCALATING:
            await handle_escalating(ctx, snap, speak)
        elif state == InterviewState.TRANSITIONING:
            await handle_transitioning(ctx, snap, speak)
        elif state == InterviewState.WRAP_UP:
            await handle_wrap_up(ctx, snap, speak)

    sim_log.info("Interview flow completed", total_questions=total)


async def handle_answer_received(
    ctx: dict, snap: SessionSnapshot, speak: SpeakFn, answer_quality: float
) -> None:
    """Called by pipeline_builder when the candidate finishes speaking."""
    total = len(ctx.get("question_bank", []))
    snap.current_state = next_state_after_listening(snap, answer_quality, total)


async def handle_silence_detected(
    ctx: dict, snap: SessionSnapshot, speak: SpeakFn
) -> None:
    """Called by SilenceDetector when the VAD silence timeout fires."""
    await handle_silence(ctx, snap, speak)