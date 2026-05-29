"""
services/session_reporter.py
-----------------------------
HTTP POST of final session metadata to Node.js when a simulation completes.

Architecture step 9: "Interview ends — Pipecat sends full transcript +
metadata to Node.js". Transcript chunks are already streamed via WebSocket
throughout the session; this call signals Node.js to finalize the DB record
and enqueue the BullMQ evaluation job.
"""

import time
import httpx

from config import config
from state_machine.states import SessionSnapshot
from utils.logger import get_logger

log = get_logger(__name__)

_HEADERS = {"Authorization": f"Bearer {config.node_api.internal_secret}"}


async def report_completed(ctx: dict, snap: SessionSnapshot) -> None:
    """
    POST session-end metadata to Node.js.

    Node.js uses this payload to:
      - Mark the SimulationSession as ended in PostgreSQL
      - Trigger BullMQ evaluation job (answer scoring, report generation)
      - Compute final integrity score from accumulated proctoring flags

    Args:
        ctx:  Full simulation context (provides simulation_id and config).
        snap: Final session snapshot — carries scores, escalation count, etc.
    """
    sim_id = ctx["simulation_id"]
    payload = {
        "simulation_id": sim_id,
        "ended_at": time.time(),
        "total_questions_asked": snap.current_question_index + 1,
        "escalation_count": snap.escalation_count,
        "answer_scores": snap.answer_scores,
        "final_pressure_score": snap.pressure_score,
        "silence_strikes": snap.silence_strikes,
        "mode": ctx.get("mode", "full"),
        "persona": ctx.get("persona"),
        "difficulty": ctx.get("difficulty", "standard"),
    }
    url = f"{config.node_api.base_url}/api/v1/sessions/{sim_id}/complete"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.post(url, headers=_HEADERS, json=payload)
            r.raise_for_status()
            log.info("Session completion reported to Node.js", simulation_id=sim_id)
        except Exception as e:
            # Non-fatal — transcript was already streamed; Node.js can still evaluate
            log.error("Session report POST failed", simulation_id=sim_id, error=str(e))