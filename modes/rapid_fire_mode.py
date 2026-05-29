"""
modes/rapid_fire_mode.py
------------------------
Rapid Fire Mode — 5 questions, 10 minutes, high pressure.
PRD §6.7: "5 questions in 10 minutes. Confidence and agility training."

Trims the question bank to 5 and enforces a 10-minute cap.
Node.js should pre-sort the question bank by priority so the 5 most
important questions are first. Pressure Multiplier is always on.
"""

from utils.logger import get_logger

log = get_logger(__name__)

_RAPID_FIRE_DURATION_MINUTES = 10
_RAPID_FIRE_MAX_QUESTIONS = 5


def is_rapid_fire_mode(ctx: dict) -> bool:
    return ctx.get("mode") == "rapid_fire"


def apply_rapid_fire_overrides(ctx: dict) -> dict:
    """
    Trim question bank to 5 questions and set a 10-minute hard duration.
    Pressure Multiplier is forced on — Rapid Fire is always maximum pace.

    Node.js is responsible for ordering the question bank before passing
    context to the agent. The first 5 questions are used.
    """
    original_bank = ctx.get("question_bank", [])
    ctx["question_bank"] = original_bank[:_RAPID_FIRE_MAX_QUESTIONS]
    ctx["duration_minutes"] = _RAPID_FIRE_DURATION_MINUTES
    ctx["pressure_multiplier"] = True

    log.info(
        "Rapid Fire mode overrides applied",
        simulation_id=ctx.get("simulation_id"),
        original_question_count=len(original_bank),
        questions_used=len(ctx["question_bank"]),
        duration_minutes=_RAPID_FIRE_DURATION_MINUTES,
    )
    return ctx