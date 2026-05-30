"""
pipeline/session_events.py
---------------------------
LiveKit transport event handlers for one simulation session.
Extracted from pipeline_builder to keep it under 100 lines and to centralise
all transport event wiring in one place.
"""

import asyncio
from pipeline.speaking_gate import SpeakingGate
from state_machine.states import InterviewState, SessionSnapshot


def register_session_events(
    transport,
    snap: SessionSnapshot,
    runner,
    sim_log,
    gate: SpeakingGate,
    participant_joined: asyncio.Event,
) -> None:
    """Register all LiveKit transport event handlers for a simulation session."""

    @transport.event_handler("on_participant_joined")
    async def on_joined(*args):
        sim_log.info("Candidate joined room")
        participant_joined.set()

    @transport.event_handler("on_participant_left")
    async def on_left(*args):
        sim_log.info("Candidate left room")
        snap.current_state = InterviewState.COMPLETED
        await runner.stop()

    @transport.event_handler("on_bot_started_speaking")
    async def on_speaking_start(*args):
        gate.started()

    @transport.event_handler("on_bot_stopped_speaking")
    async def on_speaking_stop(*args):
        gate.stopped()
