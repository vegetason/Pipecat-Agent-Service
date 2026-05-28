"""
state_machine/pressure.py
--------------------------
Pressure score computation and all transition decision functions.
Pure logic — no side effects, no I/O. Easy to unit test in isolation.
"""

from config import config
from state_machine.states import SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)


def compute_pressure_score(snapshot: SessionSnapshot) -> float:
    """
    Rolling weighted average of answer scores.
    More weight on recent answers. Returns 0.0 - 1.0.
    """
    scores = snapshot.answer_scores
    if not scores:
        return 0.0
    weights = list(range(1, len(scores) + 1))
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    score = round(weighted_sum / sum(weights), 3)
    log.debug(
        "Pressure score computed",
        simulation_id=snapshot.simulation_id,
        score=score,
        answer_count=len(scores),
    )
    return score


def should_escalate(snapshot: SessionSnapshot) -> bool:
    """True if candidate is performing above threshold and max not hit."""
    at_limit = snapshot.escalation_count >= config.pressure.max_escalations
    return snapshot.pressure_score >= config.pressure.escalation_trigger_score and not at_limit


def should_follow_up(snapshot: SessionSnapshot) -> bool:
    """True if follow-up cap for this question hasn't been reached."""
    return snapshot.current_followup_count < config.simulation.max_followups_per_question


def should_move_on(snapshot: SessionSnapshot, total_questions: int) -> bool:
    return snapshot.current_question_index < total_questions - 1


def is_final_question(snapshot: SessionSnapshot, total_questions: int) -> bool:
    return snapshot.current_question_index >= total_questions - 1