"""
modes/ghost_mode.py
------------------
Ghost Mode — post-simulation. Generates ideal answers via Groq,
synthesizes them with ElevenLabs voice clone, and returns side-by-side
comparison with the candidate''s actual answers.
"""

from groq import AsyncGroq
from config import config
from utils.logger import get_logger

log = get_logger(__name__)
_client = AsyncGroq(api_key=config.groq.api_key)

_GHOST_PROMPT = (
    "You are the ideal version of this candidate answering interview questions. "
    "Your answer must be confident, structured, concrete, and use the STAR method "
    "(Situation, Task, Action, Result) where applicable. No filler words. "
    "No hesitation. Every claim is backed by a real example. "
    "You sound like the best version of the candidate — not a different person."
)


def is_ghost_mode(ctx: dict) -> bool:
    """Check if the current simulation context is for Ghost Mode."""
    return ctx.get("mode") == "ghost"


async def generate_ideal_answer(question: str, candidate_profile: str) -> str:
    """Generate one ideal answer using Groq with the ghost persona prompt."""
    prompt = (
        f"Candidate background: {candidate_profile}\n\n"
        f"Question: {question}\n\nGive the ideal answer:"
    )
    try:
        response = await _client.chat.completions.create(
            model=config.groq.model,
            max_tokens=config.groq.ghost_mode_max_tokens,
            temperature=0.5,
            messages=[
                {"role": "system", "content": _GHOST_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        log.error("Ideal answer generation failed", error=str(e))
        return ""


async def generate_all_ideal_answers(ctx: dict) -> list[dict]:
    """Generate ideal answers for every question in the bank."""
    profile = ctx.get("candidate_profile", {})
    cv = profile.get("cv_text", "")
    questions = ctx.get("question_bank", [])
    results: list[dict] = []
    for q in questions:
        ideal = await generate_ideal_answer(q["question"], cv)
        results.append({"question": q["question"], "ideal_answer": ideal})
    return results
