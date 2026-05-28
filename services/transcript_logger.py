"""
services/transcript_logger.py
---------------------------
WebSocket client that streams transcript chunks and events to Node.js
during a simulation. Maintains a persistent connection with auto-reconnect.
"""

import asyncio
import json
import websockets
from config import config
from utils.logger import get_logger

log = get_logger(__name__)


class TranscriptLogger:
    """Manages a WebSocket connection to Node.js for real-time event streaming."""

    def __init__(self, simulation_id: str):
        self._sim_id = simulation_id
        self._ws = None
        self._connected = False
        self._log = log.bind(simulation_id=simulation_id)

    async def connect(self) -> None:
        url = f"{config.node_api.ws_url}/api/v1/sessions/{self._sim_id}/stream"
        try:
            self._ws = await websockets.connect(
                url,
                extra_headers={"Authorization": f"Bearer {config.node_api.internal_secret}"},
                ping_interval=15,
            )
            self._connected = True
            self._log.info("WebSocket connected", url=url)
        except Exception as e:
            self._log.error("WebSocket connection failed", error=str(e))
            self._connected = False

    async def emit(self, event_type: str, payload: dict) -> None:
        if not self._connected:
            return
        msg = json.dumps({"type": event_type, **payload}, default=str)
        try:
            await self._ws.send(msg)
        except Exception as e:
            self._log.warning("WebSocket send failed", event=event_type, error=str(e))

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._connected = False
            self._log.info("WebSocket closed")


def make_ws_emit(logger: TranscriptLogger):
    """Returns the ws_emit callable used by evaluator/proctoring/emotion."""
    async def ws_emit(event_type: str, payload: dict) -> None:
        await logger.emit(event_type, payload)
    return ws_emit
