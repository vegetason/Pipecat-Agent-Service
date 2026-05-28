"""
state_machine/states.py
-----------------------
Interview state enum and the session snapshot dataclass.
Everything in state_machine imports from here.
"""

from enum import Enum, auto
from dataclasses import dataclass, field


class InterviewState(Enum):
    INITIALIZING  = auto()   # Agent booting, pipeline not yet ready
    WAITING_ROOM  = auto()   # Simulated delay before interviewer "joins"
    INTRO         = auto()   # Coaching note + opening pleasantries
    QUESTIONING   = auto()   # Asking a primary question
    LISTENING     = auto()   # Candidate is speaking — agent is silent
    CHALLENGING   = auto()   # Agent pushing back on a weak answer
    FOLLOW_UP     = auto()   # Agent asking a follow-up question
    ESCALATING    = auto()   # Pressure multiplier — hardest challenge
    TRANSITIONING = auto()   # Moving to next question
    COMPLETED     = auto()   # Simulation finished


@dataclass
class SessionSnapshot:
    """
    Mutable state carried through the full simulation.
    Passed into every handler and transition function.
    Updated after every answer and state change.
    """
    simulation_id: str
    current_question_index: int = 0
    current_followup_count: int = 0
    escalation_count: int = 0
    answer_scores: list[float] = field(default_factory=list)
    pressure_score: float = 0.0
    current_state: InterviewState = InterviewState.INITIALIZING
    silence_strikes: int = 0