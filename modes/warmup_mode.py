"""
modes/warmup_mode.py
-------------------
Warmup Mode — optional 3-5 minute warmup before the real simulation.
Uses a softer persona, gives live feedback on pace/clarity/filler words.
Unscored and unrecorded — the only place softness is allowed.
"""

from utils.logger import get_logger

log = get_logger(__name__)

_WARMUP_QUESTIONS = [
    "Tell me a little about what you do.",
    "What brings you here today?",
    "What are you most excited about right now?",
]

_WARMUP_PERSONA_PROMPT = (
    "You are a supportive, encouraging interviewer running a warmup session. "
    "You are friendly and low-pressure. Give gentle live feedback on the "
    "candidate's pace, clarity, and any filler words you notice. "
    "Your tone is warm but still professional. This is unscored practice — "
    "help the candidate feel ready for the real simulation ahead."
)


def is_warmup_mode(ctx: dict) -> bool:
    """Check if warmup mode is enabled."""
    return ctx.get("mode") == "warmup"


def warmup_questions() -> list[dict]:
    """Return the short warmup question bank."""
    return [{"question": q, "type": "warmup"} for q in _WARMUP_QUESTIONS]


def warmup_persona_prompt() -> str:
    """Return the softer warmup persona system prompt."""
    return _WARMUP_PERSONA_PROMPT
