"""
services/heartbeat.py
---------------------
Sends periodic heartbeat pings to Node.js via WebSocket so it knows the
Pipecat agent is still alive. Without this, Node.js cannot distinguish a
healthy long-running simulation from a crashed agent.

Runs as a background asyncio task alongside proctoring_agent.
Stopped by setting the shared stop_event when the simulation ends.
"""

import asyncio
import time
from typing import Callable, Awaitable

from config import config
from utils.logger import get_logger

log = get_logger(__name__)

WsEmit = Callable[[str, dict], Awaitable[None]]


async def run_heartbeat(
    simulation_id: str,
    ws_emit: WsEmit,
    stop_event: asyncio.Event,
) -> None:
    """
    Emit a heartbeat WebSocket event every heartbeat_interval seconds.
    Stops cleanly when stop_event is set (simulation completed or crashed).

    Args:
        simulation_id: Used in heartbeat payload for Node.js routing.
        ws_emit:       Async function that sends events to Node.js WebSocket.
        stop_event:    Shared event set by pipeline_builder on simulation end.
    """
    sim_log = log.bind(simulation_id=simulation_id)
    interval = config.node_api.heartbeat_interval
    sim_log.info("Heartbeat started", interval_seconds=interval)

    while not stop_event.is_set():
        try:
            await ws_emit("heartbeat", {
                "simulation_id": simulation_id,
                "ts": time.time(),
            })
        except Exception as e:
            sim_log.warning("Heartbeat emit failed", error=str(e))

        # Use wait_for so we don't sleep past a stop signal
        try:
            await asyncio.wait_for(
                asyncio.shield(stop_event.wait()),
                timeout=float(interval),
            )
        except asyncio.TimeoutError:
            pass   # Normal — continue to next heartbeat

    sim_log.info("Heartbeat stopped")