"""
subagents/proctoring_agent.py
------------------------------
Background monitor that watches the camera and audio feed during a simulation.
Runs as a separate asyncio task — never touches the voice pipeline.

Emits proctoring_flag WebSocket events to Node.js in real time.
Node.js accumulates flags and computes an integrity_score in the report.
"""

import asyncio
import time
from typing import Callable, Awaitable

from subagents.proctoring_rules import ProctoringFlag
from subagents.check_runner import run_all_checks
from utils.logger import get_logger

log = get_logger(__name__)

WsEmit = Callable[[str, dict], Awaitable[None]]
# Injected signal reader — returns a dict of current sensor values
SignalReader = Callable[[], Awaitable[dict]]

# How often the proctoring agent samples the signal (seconds)
_SAMPLE_INTERVAL = 3.0


async def _emit_flag(
    flag: ProctoringFlag, sim_id: str, ws_emit: WsEmit, sim_log
) -> None:
    sim_log.warning(
        "Proctoring flag fired",
        flag_type=flag.flag_type,
        severity=flag.severity,
    )
    await ws_emit("proctoring_flag", {
        "simulation_id": sim_id,
        "flag_type": flag.flag_type,
        "severity": flag.severity,
        "detail": flag.detail,
        "timestamp": time.time(),
    })


async def _establish_baseline(read_signal: SignalReader) -> float:
    """
    Sample pitch for 60 seconds to establish a voice baseline.
    Returns mean pitch in Hz.
    """
    readings: list[float] = []
    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        signal = await read_signal()
        pitch = signal.get("current_pitch_hz", 0.0)
        if pitch > 0:
            readings.append(pitch)
        await asyncio.sleep(_SAMPLE_INTERVAL)
    return sum(readings) / len(readings) if readings else 0.0


async def run_proctoring(
    simulation_id: str,
    read_signal: SignalReader,
    ws_emit: WsEmit,
    stop_event: asyncio.Event,
) -> None:
    """
    Main proctoring loop. Runs until stop_event is set (simulation ends).

    Args:
        simulation_id: For logging and WebSocket events.
        read_signal:   Async fn that returns current camera/audio signal dict.
        ws_emit:       WebSocket emit fn to Node.js.
        stop_event:    Set by pipeline_builder when simulation completes.
    """
    sim_log = log.bind(simulation_id=simulation_id)
    sim_log.info("Proctoring agent started")

    baseline_pitch = await _establish_baseline(read_signal)
    sim_log.info("Voice baseline established", pitch_hz=round(baseline_pitch, 1))

    while not stop_event.is_set():
        try:
            signal = await read_signal()
            signal["baseline_pitch_hz"] = baseline_pitch
            flags = run_all_checks(signal)
            for flag in flags:
                await _emit_flag(flag, simulation_id, ws_emit, sim_log)
        except Exception as e:
            sim_log.error("Proctoring sample failed", error=str(e))
        await asyncio.sleep(_SAMPLE_INTERVAL)

    sim_log.info("Proctoring agent stopped")