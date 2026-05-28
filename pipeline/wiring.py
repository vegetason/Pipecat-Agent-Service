"""
pipeline/wiring.py
-----------------
Pipeline event wiring and background task spawning.
Extracted from pipeline_builder.py to keep it under 100 lines.
"""

import asyncio
from typing import Callable, Awaitable

from utils.logger import get_logger

log = get_logger(__name__)


def wire_pipeline(
    stt, transport, runner, sim_id: str, sim_log,
    on_candidate_speech, ws_emit, emotion_state: dict,
    speak,
) -> tuple:
    """Attach event handlers and spawn background agents. Returns (proctoring_task, stop_event)."""

    @stt.event_handler("on_transcription_message")
    async def on_transcript(message: dict):
        transcript = message.get("text", "").strip()
        if transcript:
            ws_emit("transcript_chunk", {
                "simulation_id": sim_id,
                "text": transcript,
            })
        await on_candidate_speech(message, sim_log)

    async def on_state_change(new_state) -> None:
        stress = emotion_state.get("stress_level", 0.0)
        tag = emotion_state.get("emotion_tag", "calm")
        if stress > 0.0 or tag != "calm":
            await ws_emit("emotion_context", {
                "simulation_id": sim_id,
                "stress_level": stress,
                "emotion_tag": tag,
                "state": new_state.name,
            })

    @transport.event_handler("on_participant_left")
    async def on_left(participant: dict, reason: str):
        sim_log.info("Candidate left room", reason=reason)
        await runner.stop()

    stop_event = asyncio.Event()

    async def read_signal() -> dict:
        return {"face_count": 1, "gaze_x": 0.0, "gaze_y": 0.0,
                "noise_db": 30.0, "current_pitch_hz": 120.0}

    from subagents.proctoring_agent import run_proctoring
    proctoring_task = asyncio.create_task(
        run_proctoring(sim_id, read_signal, ws_emit, stop_event)
    )

    return proctoring_task, stop_event, on_state_change
