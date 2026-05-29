"""
state_machine/challenge_handlers.py
----------------------------------
Handlers for CHALLENGING, FOLLOW_UP, ESCALATING, and TRANSITIONING states.
Extracted from state_machine/handlers.py to keep each file under 100 lines.
"""

from typing import Callable, Awaitable

from config import config
from context.context_builder import build_system_prompt
from state_machine.states import InterviewState, SessionSnapshot

SpeakFn = Callable[[str], Awaitable[None]]


async def handle_challenging(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    prompt = build_system_prompt(ctx)
    instruction = (
        f"{prompt}\n\nThe candidate gave a weak or vague answer. "
        f"Challenge it directly. Demand a specific concrete example."
    )
    await speak(instruction)
    snapshot.current_followup_count += 1
    snapshot.current_state = InterviewState.LISTENING


async def handle_follow_up(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    questions = ctx.get("question_bank", [])
    q = questions[snapshot.current_question_index]
    follow_ups = q.get("follow_up_bank", [])
    count = snapshot.current_followup_count
    follow_up = follow_ups[count] if count < len(follow_ups) else None
    prompt = build_system_prompt(ctx)
    instruction = (
        f"{prompt}\n\nAsk this follow-up: '{follow_up}'"
        if follow_up else
        f"{prompt}\n\nAsk a natural probing follow-up on the candidate's last answer."
    )
    await speak(instruction)
    snapshot.current_followup_count += 1
    snapshot.current_state = InterviewState.LISTENING


async def handle_escalating(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    bank = ctx.get("escalation_bank", [])
    challenge = bank[snapshot.escalation_count % len(bank)] if bank else (
        "Let me stop you there — what is the core assumption you are making?"
    )
    prompt = build_system_prompt(ctx)
    instruction = f"{prompt}\n\nDeliver this pressure challenge: '{challenge}'"
    await speak(instruction)
    snapshot.escalation_count += 1
    snapshot.current_state = InterviewState.LISTENING


async def handle_transitioning(ctx: dict, snapshot: SessionSnapshot, speak: SpeakFn) -> None:
    snapshot.current_question_index += 1
    snapshot.current_followup_count = 0
    snapshot.silence_strikes = 0
    prompt = build_system_prompt(ctx)
    instruction = (
        f"{prompt}\n\nAcknowledge the previous answer in one sentence, "
        f"then move directly to the next question."
    )
    await speak(instruction)
    snapshot.current_state = InterviewState.QUESTIONING
