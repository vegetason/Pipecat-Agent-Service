"""
state_machine/handlers.py
--------------------------
One async handler function per interview state.
Each handler makes the agent speak and updates the snapshot.
Imported by interview_flow.py — nothing else should call these directly.
"""

import asyncio
import random
from typing import Callable, Awaitable

from context.context_builder import build_system_prompt
from state_machine.states import InterviewState, SessionSnapshot

SpeakFn = Callable[[str], Awaitable[None]]


async def handle_waiting_room(snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    """Brief natural pause after candidate joins, before the interviewer speaks."""
    await asyncio.sleep(random.randint(2, 4))


async def handle_intro(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    prompt = build_system_prompt(ctx)
    instruction = (
        f"{prompt}\n\nStart the simulation now. Deliver the coaching note from the "
        f"'Opening Coaching Note' section naturally, then say: "
        f"'Let's begin. Take a moment to get comfortable.'"
    )
    await speak(instruction)
    snapshot.current_state = InterviewState.QUESTIONING


async def handle_questioning(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    questions = ctx.get("question_bank", [])
    q = questions[snapshot.current_question_index]
    prompt = build_system_prompt(ctx)
    instruction = f"{prompt}\n\nAsk this question now: '{q['question']}'"
    await speak(instruction)
    snapshot.current_state = InterviewState.LISTENING


async def handle_silence(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    if snapshot.silence_strikes == 0:
        await speak("Take your time.")
        snapshot.silence_strikes += 1
    else:
        await speak("Let's move on.")
        snapshot.current_state = InterviewState.TRANSITIONING


async def handle_wrap_up(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    prompt = build_system_prompt(ctx)
    instruction = (
        f"{prompt}\n\nThe interview is now complete. Close it out naturally — "
        f"thank the candidate warmly but professionally, describe fictional next steps "
        f"(e.g. 'We will be in touch within the week'), and say goodbye."
    )
    await speak(instruction)
    snapshot.current_state = InterviewState.COMPLETED
