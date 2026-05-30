"""
pipeline/session_events.py
---------------------------
LiveKit transport event handlers for one simulation session.
Extracted from pipeline_builder to keep it under 100 lines and to centralise
all transport event wiring in one place.

Correct pipecat 1.3 event names (from memory file):
  - on_first_participant_joined  (NOT on_participant_joined — silently never fires)
  - on_participant_left          (fires on disconnect)
  - on_bot_started_speaking
  - on_bot_stopped_speaking

Correct runner method:
  - runner.cancel()              (NOT runner.stop() — raises AttributeError)
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

    @transport.event_handler("on_first_participant_joined")
    async def on_joined(*args):
        """
        Fires when the first remote participant connects.
        Sets the participant_joined event to unblock run_interview().

        NOTE: Must be on_first_participant_joined, NOT on_participant_joined.
        on_participant_joined does not exist in pipecat 1.3 LiveKit transport
        and silently never fires, causing the interview to time out after 300s.
        """
        sim_log.info("Candidate joined room")
        participant_joined.set()

    @transport.event_handler("on_participant_left")
    async def on_left(*args):
        """
        Fires when a remote participant disconnects.
        Marks the simulation complete and cancels the runner.

        NOTE: runner.cancel() is correct for WorkerRunner in pipecat 1.3.
        runner.stop() does NOT exist and raises AttributeError, which pipecat
        catches internally and logs — leaving the pipeline orphaned until timeout.
        """
        sim_log.info("Candidate left room")
        snap.current_state = InterviewState.COMPLETED
        await runner.cancel()

    @transport.event_handler("on_bot_started_speaking")
    async def on_speaking_start(*args):
        """
        Fires when TTS audio begins playing.
        Clears the SpeakingGate so TranscriptRouter drops incoming transcriptions
        while the agent is mid-sentence.
        """
        gate.started()

    @transport.event_handler("on_bot_stopped_speaking")
    async def on_speaking_stop(*args):
        """
        Fires when TTS audio finishes playing.
        Sets the SpeakingGate, unblocking speak() in llm_client and allowing
        TranscriptRouter to accept candidate transcriptions again.
        """
        gate.stopped()