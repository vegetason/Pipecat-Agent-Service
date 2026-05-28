"""
context/context_builder.py
--------------------------
Assembles the full LLM system prompt for the AI interviewer.

The prompt has five sections joined together:
  Role → Candidate Profile → Interview Rules → Weakness Coaching → Emotion Modifier
Section builders live in context/section_builders.py.
"""

from utils.logger import get_logger
from context.section_builders import (
    build_role_section,
    build_candidate_section,
    build_rules_section,
    build_weakness_section,
    build_emotion_section,
)

log = get_logger(__name__)


def build_system_prompt(
    ctx: dict,
    stress_level: float = 0.0,
    emotion_tag: str = "calm",
) -> str:
    """
    Build the complete LLM system prompt for the interviewer agent.

    Args:
        ctx:          Full simulation context.
        stress_level: Live stress score from emotion_analyzer (0.0 - 1.0).
        emotion_tag:  Current emotion label from emotion_analyzer.
    Returns:
        A single system prompt string ready to pass to Claude.
    """
    persona = ctx.get("persona", "corporate_executive")
    profile = ctx.get("candidate_profile", {})
    patterns = ctx.get("weakness_patterns", [])
    difficulty = ctx.get("difficulty", "standard")

    sections = [
        build_role_section(persona, difficulty),
        build_candidate_section(profile),
        build_rules_section(ctx),
        build_weakness_section(patterns),
        build_emotion_section(emotion_tag, stress_level),
    ]

    prompt = "\n\n".join(s for s in sections if s)
    log.debug("System prompt built", persona=persona, emotion=emotion_tag,
              stress=round(stress_level, 2))
    return prompt
