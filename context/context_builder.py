"""
context/context_builder.py
--------------------------
Assembles the full LLM system prompt for the AI interviewer.

Called twice:
  1. At simulation start — build_system_prompt(ctx)
  2. When emotion state changes — build_system_prompt(ctx, stress_level, emotion_tag)

The prompt has five sections that are joined together:
  Role → Candidate Profile → Interview Rules → Weakness Coaching → Emotion Modifier
"""

from context.personas import PERSONA_PROMPTS
from utils.logger import get_logger

log = get_logger(__name__)

# How the agent should adapt its behavior for each detected emotion state
_EMOTION_MODIFIERS: dict[str, str] = {
    "anxious": (
        "The candidate is visibly stressed right now. Soften your tone very slightly "
        "— say 'Take your time' once if there is a long pause. Do not reduce difficulty."
    ),
    "overconfident": (
        "The candidate sounds rehearsed and overconfident. Push back harder. "
        "Say: 'That sounds like a prepared answer — give me a real example from "
        "your own experience, not a textbook one.'"
    ),
    "confused": (
        "The candidate seems genuinely confused. Rephrase the question once, "
        "differently. Do not rephrase a second time — move on if they are still stuck."
    ),
    "disengaged": (
        "The candidate sounds flat and disengaged. Increase your directness and "
        "energy to pull them back in: 'Walk me through that in much more detail.'"
    ),
    "calm": "",  # No modifier needed
}


def build_system_prompt(
    ctx: dict,
    stress_level: float = 0.0,
    emotion_tag: str = "calm",
) -> str:
    """
    Build the complete LLM system prompt for the interviewer agent.

    Args:
        ctx:          Full simulation context (from fixture or Node.js payload).
        stress_level: Live stress score from emotion_analyzer (0.0 - 1.0).
        emotion_tag:  Current emotion label from emotion_analyzer.

    Returns:
        A single system prompt string ready to pass to Claude.
    """
    persona  = ctx.get("persona", "corporate_executive")
    profile  = ctx.get("candidate_profile", {})
    patterns = ctx.get("weakness_patterns", [])
    difficulty = ctx.get("difficulty", "standard")

    sections = [
        _role_section(persona, difficulty),
        _candidate_section(profile),
        _rules_section(ctx),
        _weakness_section(patterns),
        _emotion_section(emotion_tag, stress_level),
    ]

    prompt = "\n\n".join(s for s in sections if s)
    log.debug("System prompt built", persona=persona, emotion=emotion_tag, stress=round(stress_level, 2))
    return prompt


# ---------------------------------------------------------------------------
# Private section builders — each returns a string or ""
# ---------------------------------------------------------------------------

def _role_section(persona: str, difficulty: str) -> str:
    base = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["custom"])
    suffix = " Be maximally unforgiving — this is nightmare difficulty." if difficulty == "nightmare" else ""
    return f"## Your Role\n{base}{suffix}"


def _candidate_section(profile: dict) -> str:
    if not profile:
        return ""
    name  = profile.get("name", "the candidate")
    role  = profile.get("target_role", "the role")
    cv    = profile.get("cv_text", "No CV provided.")
    return (
        f"## Candidate Profile\n"
        f"You are interviewing {name} for the position of {role}.\n"
        f"Their background: {cv}\n"
        f"Reference their actual experience in your questions. "
        f"Probe any CV gaps or inconsistencies directly."
    )


def _rules_section(ctx: dict) -> str:
    max_fu = ctx.get("max_followups_per_question", 2)
    return (
        f"## Interview Rules\n"
        f"- Never accept vague answers — always demand specifics and concrete examples.\n"
        f"- Push back on weak answers — make the candidate defend their position.\n"
        f"- Detect rehearsed answers and dig underneath them.\n"
        f"- Do not give hints — if the candidate is stuck, silence is your response.\n"
        f"- Maximum {max_fu} follow-up questions per main question, always on-topic.\n"
        f"- Maintain professional tone throughout. No warmth inflation.\n"
        f"- Use brief thinking pauses before responding to simulate real human rhythm."
    )


def _weakness_section(patterns: list) -> str:
    notes = [p["coaching_note"] for p in patterns if "coaching_note" in p]
    if not notes:
        return ""
    coaching = "\n".join(f"- {n}" for n in notes)
    return (
        f"## Opening Coaching Note\n"
        f"Before your first question, deliver this coaching naturally as an opener:\n"
        f"{coaching}"
    )


def _emotion_section(emotion_tag: str, stress_level: float) -> str:
    modifier = _EMOTION_MODIFIERS.get(emotion_tag, "")
    if not modifier:
        return ""
    return f"## Live Candidate State (stress={stress_level:.2f})\n{modifier}"