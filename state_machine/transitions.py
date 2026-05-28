"""
state_machine/transitions.py
-----------------------------
Single transition function — decides the next state after a candidate answers.
Imports pure logic from pressure.py and state definitions from states.py.
"""

from state_machine.states import InterviewState, SessionSnapshot
from state_machine.pressure import (
    compute_pressure_score,
    should_escalate,
    should_follow_up,
    is_final_question,
)
from utils.logger import get_logger

log = get_logger(__name__)


def next_state_after_listening(
    snapshot: SessionSnapshot,
    answer_quality: float,
    total_questions: int,
) -> InterviewState:
    """
    Core transition logic. Called after the candidate finishes speaking.

    Args:
        snapshot:       Current session state.
        answer_quality: Score for the answer just given (0.0 - 1.0).
        total_questions: Total questions in the bank.
    """
    snapshot.answer_scores.append(answer_quality)
    snapshot.pressure_score = compute_pressure_score(snapshot)

    sim_id = snapshot.simulation_id

    if answer_quality < 0.5 and should_follow_up(snapshot):
        log.info("Weak answer → CHALLENGING", simulation_id=sim_id)
        return InterviewState.CHALLENGING

    if should_escalate(snapshot):
        log.info("Pressure threshold hit → ESCALATING", simulation_id=sim_id)
        return InterviewState.ESCALATING

    if should_follow_up(snapshot):
        log.info("Follow-up available → FOLLOW_UP", simulation_id=sim_id)
        return InterviewState.FOLLOW_UP

    if is_final_question(snapshot, total_questions):
        log.info("Final question done → COMPLETED", simulation_id=sim_id)
        return InterviewState.COMPLETED

    log.info("Moving to next question → TRANSITIONING", simulation_id=sim_id)
    return InterviewState.TRANSITIONING