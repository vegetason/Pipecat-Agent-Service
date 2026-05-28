"""
modes/silent_mode.py
-------------------
Silent Mode — agent does not speak. Questions appear as text on screen.
TTS is disabled. Pipeline routes questions to the WebSocket display layer.
Feedback covers body language only.
"""

from utils.logger import get_logger

log = get_logger(__name__)


def is_silent_mode(ctx: dict) -> bool:
    """Check if the current simulation context has silent mode enabled."""
    return ctx.get("mode") == "silent"


def silent_mode_questions(ctx: dict) -> list[dict]:
    """Extract question text + per-question countdown for the display layer."""
    questions = ctx.get("question_bank", [])
    duration = ctx.get("duration_minutes", 30)
    per_q = max(30, (duration * 60) // max(len(questions), 1))
    return [
        {"question": q["question"], "time_limit_seconds": per_q}
        for q in questions
    ]


async def configure_silent_pipeline(tts, speak, ws_emit, ctx: dict) -> None:
    """
    Disable TTS output. Instead, emit question_display events
    to the Node.js WebSocket for on-screen rendering.
    """
    log.info("Configuring silent mode — TTS disabled, text display enabled")
    questions = silent_mode_questions(ctx)
    for q in questions:
        await ws_emit("question_display", {
            "simulation_id": ctx["simulation_id"],
            "question": q["question"],
            "time_limit_seconds": q["time_limit_seconds"],
        })
