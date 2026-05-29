"""
subagents/evaluator_agent.py
-----------------------------
Scores each answer as a background asyncio task — never blocks the pipeline.
Emits answer_scored to Node.js; feeds overall score back to the state machine.
"""

import asyncio
from groq import AsyncGroq
from typing import Callable, Awaitable

from config import config
from subagents.evaluator_prompt import build_evaluation_prompt, parse_scores
from state_machine.states import SessionSnapshot
from utils.logger import get_logger
from utils.error_handler import retry, ProviderError

log = get_logger(__name__)
_client = AsyncGroq(api_key=config.groq.api_key)

WsEmit = Callable[[str, dict], Awaitable[None]]


@retry(attempts=2, delay=1.0, exceptions=(ProviderError,))
async def _call_groq(prompt: str) -> str:
    try:
        r = await _client.chat.completions.create(
            model=config.groq.model,
            max_tokens=300,
            temperature=0.2,   # low temp for consistent scoring
            messages=[{"role": "user", "content": prompt}],
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        raise ProviderError("Groq/Evaluator", str(e))


async def evaluate_answer(
    ctx: dict,
    snapshot: SessionSnapshot,
    answer_transcript: str,
    ws_emit: WsEmit,
    question_index: int,
) -> float:
    """Score one answer. question_index captured at spawn time (race condition fix)."""
    sim_id = ctx["simulation_id"]
    sim_log = log.bind(simulation_id=sim_id)
    questions = ctx.get("question_bank", [])
    if question_index >= len(questions):
        sim_log.warning("Evaluation skipped — question index out of range", index=question_index)
        return 0.6
    question = questions[question_index]
    persona = ctx.get("persona", "corporate_executive")
    target_role = ctx.get("candidate_profile", {}).get("target_role", "the role")

    prompt = build_evaluation_prompt(question, answer_transcript, persona, target_role)

    try:
        raw = await _call_groq(prompt)
        scores = parse_scores(raw)
        overall = float(scores.get("overall", 0.6))
        sim_log.info("Answer scored", question_id=question.get("id"), overall=overall)
        await ws_emit("answer_scored", {
            "simulation_id": sim_id,
            "question_id": question.get("id"),
            "scores": scores,
            "overall": overall,
        })
        return overall
    except Exception as e:
        sim_log.error("Evaluation failed", error=str(e))
        return 0.6   # safe fallback — triggers follow-up, not escalation


def spawn_evaluation(
    ctx: dict,
    snapshot: SessionSnapshot,
    answer_transcript: str,
    ws_emit: WsEmit,
    on_score: Callable[[float], None],
    question_index: int,
) -> None:
    """Fire-and-forget. question_index passed explicitly to avoid race with handle_transitioning."""
    async def _run():
        score = await evaluate_answer(ctx, snapshot, answer_transcript, ws_emit, question_index)
        on_score(score)

    asyncio.create_task(_run())