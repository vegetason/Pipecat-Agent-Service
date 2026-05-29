"""
processors/emotion_analyzer.py
--------------------------------
Pipecat frame processor — samples audio every N seconds, runs emotion
inference, emits emotion_update events to Node.js, and updates the
context_builder with the latest stress state.

Runs in parallel with the main pipeline — never blocks STT → LLM → TTS.
"""

import asyncio
import time
import numpy as np
from typing import Callable, Awaitable

from pipecat.frames.frames import AudioRawFrame
from pipecat.processors.frame_processor import FrameProcessor

from processors.emotion_model import run_inference, EmotionResult
from config import config
from utils.logger import get_logger

log = get_logger(__name__)

# Callback type: receives EmotionResult and simulation_id
EmotionCallback = Callable[[EmotionResult, str], Awaitable[None]]


class EmotionAnalyzer(FrameProcessor):
    """
    Passthrough processor — audio frames flow through unchanged.
    Every N seconds a chunk is sampled and sent to emotion_model.
    """

    def __init__(self, simulation_id: str, on_emotion: EmotionCallback):
        super().__init__()
        self._sim_id = simulation_id
        self._on_emotion = on_emotion
        self._buffer: list[np.ndarray] = []
        self._last_sample_time = time.monotonic()
        self._log = log.bind(simulation_id=simulation_id)

    async def process_frame(self, frame, direction):
        # super() must be called first — handles StartFrame, CancelFrame, etc.
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        if not isinstance(frame, AudioRawFrame):
            return

        chunk = np.frombuffer(frame.audio, dtype=np.int16).astype(np.float32) / 32768.0
        self._buffer.append(chunk)

        elapsed = time.monotonic() - self._last_sample_time
        if elapsed >= config.emotion.sample_interval_seconds:
            await self._analyze()

    async def _analyze(self) -> None:
        """Run inference on buffered audio, fire callback, reset buffer."""
        if not self._buffer:
            return
        audio = np.concatenate(self._buffer)
        self._buffer = []
        self._last_sample_time = time.monotonic()

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_inference, audio
            )
            self._log.debug(
                "Emotion sample",
                stress=result.stress_level,
                tag=result.emotion_tag,
            )
            await self._on_emotion(result, self._sim_id)
        except Exception as e:
            self._log.error("Emotion inference failed", error=str(e))


def make_emotion_callback(
    ws_emit: Callable[[str, dict], Awaitable[None]],
    emotion_state: dict,
) -> EmotionCallback:
    """
    Returns the callback fired after each emotion sample.
    Updates shared emotion_state dict (read by context_builder)
    and emits emotion_update event to Node.js WebSocket.
    """
    async def on_emotion(result: EmotionResult, sim_id: str) -> None:
        emotion_state["stress_level"] = result.stress_level
        emotion_state["emotion_tag"] = result.emotion_tag
        await ws_emit("emotion_update", {
            "simulation_id": sim_id,
            "stress_level": result.stress_level,
            "emotion_tag": result.emotion_tag,
        })
    return on_emotion