"""
pipeline/pipeline_builder.py
-----------------------------
Assembles the full Pipecat pipeline with all real-time processors:
  STT → TTS core, EmotionAnalyzer, RamblingDetector,
  EvaluatorAgent, ProctoringAgent, WebSocket transport to Node.js.
"""

import asyncio

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

from pipeline.transport import create_transport
from pipeline.processors import create_stt, create_tts, create_vad
from pipeline.llm_client import make_speak_fn
from pipeline.tts_queue import drain_tts_queue
from pipeline.event_handlers import make_on_candidate_speech
from state_machine.interview_flow import run_interview
from state_machine.states import SessionSnapshot
from services.transcript_logger import TranscriptLogger, make_ws_emit
from processors.emotion_analyzer import EmotionAnalyzer, make_emotion_callback
from processors.rambling_detector import RamblingDetector, make_interrupt_callback
from subagents.proctoring_agent import run_proctoring
from modes.mode_config import apply_mode
from utils.logger import get_logger
from utils.error_handler import PipelineError

log = get_logger(__name__)


async def build_and_run(ctx: dict) -> None:
    sim_id = ctx["simulation_id"]
    sim_log = log.bind(simulation_id=sim_id)
    sim_log.info("Building pipeline", mode=ctx.get("mode"))

    # ── Core pipeline processors ──────────────────────────────────────
    transport = create_transport(ctx["room_url"], sim_id)
    stt = create_stt(sim_id)
    tts = create_tts(sim_id)
    vad = create_vad(sim_id)

    # ── WebSocket to Node.js ──────────────────────────────────────────
    ws_logger = TranscriptLogger(sim_id)
    await ws_logger.connect()
    ws_emit = make_ws_emit(ws_logger)

    # ── State, speech bridge ──────────────────────────────────────────
    tts_queue: asyncio.Queue[str] = asyncio.Queue()
    snap = SessionSnapshot(simulation_id=sim_id)
    speak = make_speak_fn(tts_queue, sim_id)

    # ── Mode-specific configuration ───────────────────────────────────
    active_modes = await apply_mode(ctx, tts, speak, ws_emit)
    sim_log.info("Modes applied", modes=active_modes)

    # ── Real-time processors ──────────────────────────────────────────
    emotion_state: dict[str, float | str] = {"stress_level": 0.0, "emotion_tag": "calm"}
    on_emotion = make_emotion_callback(ws_emit, emotion_state)
    emotion = EmotionAnalyzer(sim_id, on_emotion)

    ramble_interrupt = make_interrupt_callback(speak)
    rambling = RamblingDetector(sim_id, snap, ramble_interrupt)

    on_candidate_speech = make_on_candidate_speech(ctx, snap, speak, ws_emit)

    # ── Pipeline assembly ─────────────────────────────────────────────
    pipeline = Pipeline([
        transport.input(),
        vad,
        stt,
        emotion,    # parallel — never blocks STT → LLM → TTS
        rambling,   # monitors transcript for rambling
        tts,
        transport.output(),
    ])

    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    # ── Event wiring ──────────────────────────────────────────────────
    @stt.event_handler("on_transcription_message")
    async def on_transcript(message: dict):
        transcript = message.get("text", "").strip()
        if transcript:
            await ws_emit("transcript_chunk", {
                "simulation_id": sim_id,
                "text": transcript,
            })
        await on_candidate_speech(message, sim_log)

    # ── Emotion-aware prompt updates ──────────────────────────────────
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

    # ── Background agents ─────────────────────────────────────────────
    stop_event = asyncio.Event()

    async def read_signal() -> dict:
        return {"face_count": 1, "gaze_x": 0.0, "gaze_y": 0.0,
                "noise_db": 30.0, "current_pitch_hz": 120.0}

    proctoring_task = asyncio.create_task(
        run_proctoring(sim_id, read_signal, ws_emit, stop_event)
    )

    sim_log.info("Pipeline assembled — starting simulation")
    try:
        await asyncio.gather(
            runner.run(task),
            run_interview(ctx, speak),
            drain_tts_queue(tts_queue, tts, snap),
        )
    except Exception as e:
        sim_log.error("Pipeline crashed", error=str(e))
        raise PipelineError(str(e))
    finally:
        stop_event.set()
        proctoring_task.cancel()
        await ws_logger.close()
        sim_log.info("Pipeline shut down")
