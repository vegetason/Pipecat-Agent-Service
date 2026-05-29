"""
pipeline/background_tasks.py
-----------------------------
Spawns and returns the background asyncio tasks that run alongside the
main pipeline: proctoring monitor and heartbeat.
Extracted from pipeline_builder.py to keep that file under 100 lines.
"""

import asyncio
from typing import Callable, Awaitable

from subagents.proctoring_agent import run_proctoring
from services.heartbeat import run_heartbeat
from utils.logger import get_logger

log = get_logger(__name__)

WsEmit = Callable[[str, dict], Awaitable[None]]


async def _stub_signal() -> dict:
    """
    Placeholder signal reader used until real camera/audio sensor integration
    is wired in. Returns a clean signal — no flags will fire in dev.
    Replace with actual sensor reads (MediaPipe, WebRTC stats) in production.
    """
    return {
        "face_count": 1,
        "gaze_x": 0.0,
        "gaze_y": 0.0,
        "noise_db": 30.0,
        "current_pitch_hz": 120.0,
    }


def start_background_tasks(
    sim_id: str,
    ws_emit: WsEmit,
    stop_event: asyncio.Event,
) -> tuple[asyncio.Task, asyncio.Task]:
    """
    Spawn proctoring and heartbeat tasks. Both run until stop_event is set.

    Returns:
        (proctoring_task, heartbeat_task) — caller must cancel both in finally block.
    """
    proctoring_task = asyncio.create_task(
        run_proctoring(sim_id, _stub_signal, ws_emit, stop_event)
    )
    heartbeat_task = asyncio.create_task(
        run_heartbeat(sim_id, ws_emit, stop_event)
    )
    log.info("Background tasks started", simulation_id=sim_id)
    return proctoring_task, heartbeat_task