"""
pipeline/processor_factory.py
------------------------------
Creates the three real-time Pipecat processors injected into the pipeline:
EmotionAnalyzer, RamblingDetector, SilenceDetector.

Extracted from pipeline_builder.py so that file stays under 100 lines
after silence detection, heartbeat, and session reporter were added.
"""

from typing import Callable, Awaitable

from processors.emotion_analyzer import EmotionAnalyzer, make_emotion_callback
from processors.rambling_detector import RamblingDetector, make_interrupt_callback
from pipeline.silence_detector import SilenceDetector
from state_machine.states import SessionSnapshot

WsEmit = Callable[[str, dict], Awaitable[None]]


def create_processors(
    sim_id: str,
    ctx: dict,
    snap: SessionSnapshot,
    speak: Callable,
    ws_emit: WsEmit,
) -> tuple[EmotionAnalyzer, RamblingDetector, SilenceDetector, dict]:
    """
    Instantiate all real-time processors for one simulation session.

    Args:
        sim_id:  Simulation ID for logging.
        ctx:     Full simulation context (needed by SilenceDetector).
        snap:    Shared session snapshot (must be the SAME object used by
                 interview_flow and event_handlers — state changes need to be visible).
        speak:   TTS bridge function (used by rambling/silence interrupt callbacks).
        ws_emit: WebSocket emit to Node.js (used by emotion callback).

    Returns:
        (emotion, rambling, silence, emotion_state)
        emotion_state is a shared mutable dict read by context_builder on each LLM call.
    """
    # Shared dict — written by EmotionAnalyzer, read by context_builder per LLM prompt
    emotion_state: dict = {"stress_level": 0.0, "emotion_tag": "calm"}

    on_emotion = make_emotion_callback(ws_emit, emotion_state)
    emotion = EmotionAnalyzer(sim_id, on_emotion)

    ramble_interrupt = make_interrupt_callback(speak)
    rambling = RamblingDetector(sim_id, snap, ramble_interrupt)

    silence = SilenceDetector(ctx, snap, speak)

    return emotion, rambling, silence, emotion_state