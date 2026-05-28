"""
context/section_builders.py
--------------------------
Private section builder functions extracted from context_builder.py.
Each builds one section of the LLM system prompt.
"""

from context.personas import PERSONA_PROMPTS

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
    "calm": "",
}


def build_role_section(persona: str, difficulty: str) -> str:
    base = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["custom"])
    suffix = ""
    if difficulty == "nightmare":
        suffix = " Be maximally unforgiving — this is nightmare difficulty."
    return f"## Your Role\n{base}{suffix}"


def build_candidate_section(profile: dict) -> str:
    if not profile:
        return ""
    name = profile.get("name", "the candidate")
    role = profile.get("target_role", "the role")
    cv = profile.get("cv_text", "No CV provided.")
    return (
        f"## Candidate Profile\n"
        f"You are interviewing {name} for the position of {role}.\n"
        f"Their background: {cv}\n"
        f"Reference their actual experience in your questions. "
        f"Probe any CV gaps or inconsistencies directly."
    )


def build_rules_section(ctx: dict) -> str:
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


def build_weakness_section(patterns: list) -> str:
    notes = [p["coaching_note"] for p in patterns if "coaching_note" in p]
    if not notes:
        return ""
    coaching = "\n".join(f"- {n}" for n in notes)
    return (
        f"## Opening Coaching Note\n"
        f"Before your first question, deliver this coaching naturally as an opener:\n"
        f"{coaching}"
    )


def build_emotion_section(emotion_tag: str, stress_level: float) -> str:
    modifier = _EMOTION_MODIFIERS.get(emotion_tag, "")
    if not modifier:
        return ""
    return f"## Live Candidate State (stress={stress_level:.2f})\n{modifier}"
