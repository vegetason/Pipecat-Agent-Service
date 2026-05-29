"""
pipeline/pipeline_builder.py
-----------------------------
Assembles and runs the full Pipecat pipeline for one simulation session.

Processor creation  → pipeline/processor_factory.py
Silence detection   → pipeline/silence_detector.py
Background tasks    → pipeline/background_tasks.py
Session finalizer   → services/session_reporter.py
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
from pipeline.processor_factory import create_processors
from pipeline.background_tasks import start_background_tasks
from state_machine.interview_flow import run_interview
from state_machine.states import SessionSnapshot
from services.transcript_logger import TranscriptLogger, make_ws_emit
from services.session_reporter import report_completed
from modes.mode_config import apply_mode
from utils.logger import get_logger
from utils.error_handler import PipelineError

log = get_logger(__name__)


async def build_and_run(ctx: dict) -> None:
    sim_id = ctx["simulation_id"]
    sim_log = log.bind(simulation_id=sim_id)
    sim_log.info("Building pipeline", mode=ctx.get("mode"))

    # Create processors
    stt, tts, vad = create_stt(sim_id), create_tts(sim_id), create_vad(sim_id)

    # Create transport with VAD attached
    transport = create_transport(ctx, vad_analyzer=vad)

    # WebSocket transcript logger
    ws_logger = TranscriptLogger(sim_id)
    await ws_logger.connect()
    ws_emit = make_ws_emit(ws_logger)

    # TTS queue and shared session snapshot
    tts_queue: asyncio.Queue[str] = asyncio.Queue()
    snap = SessionSnapshot(simulation_id=sim_id)
    speak = make_speak_fn(tts_queue, sim_id)

    # Apply any active modes (emotion, rambling, etc.)
    active_modes = await apply_mode(ctx, tts, speak, ws_emit)
    sim_log.info("Modes applied", modes=active_modes)

    # Create special processors (emotion, rambling, silence)
    emotion, rambling, silence, _ = create_processors(sim_id, ctx, snap, speak, ws_emit)
    on_candidate_speech = make_on_candidate_speech(ctx, snap, speak, ws_emit)

    # STT event handler
    @stt.event_handler("on_transcription_message")
    async def on_transcript(message: dict):
        text = message.get("text", "").strip()
        if text:
            await ws_emit("transcript_chunk", {"simulation_id": sim_id, "text": text})
        await on_candidate_speech(message, sim_log)

    # Pipeline runner (must be defined before the event handler that uses it)
    runner = PipelineRunner()

    # Transport event handler (uses runner)
    @transport.event_handler("on_participant_left")
    async def on_left(participant: dict, reason: str):
        sim_log.info("Candidate left room", reason=reason)
        await runner.stop()

    # Build pipeline – note: vad is NOT in this list, it's attached to transport.input()
    pipeline = Pipeline([
        transport.input(),
        stt,
        emotion,
        rambling,
        silence,
        tts,
        transport.output(),
    ])
    task = PipelineTask(pipeline)

    # Background tasks (proctoring & heartbeat)
    stop_event = asyncio.Event()
    proctoring_task, heartbeat_task = start_background_tasks(sim_id, ws_emit, stop_event)

    sim_log.info("Pipeline assembled — starting simulation")
    try:
        await asyncio.gather(
            runner.run(task),
            run_interview(ctx, speak, snap),
            drain_tts_queue(tts_queue, tts, snap),
        )
    except Exception as e:
        sim_log.error("Pipeline crashed", error=str(e))
        raise PipelineError(str(e))
    finally:
        stop_event.set()
        proctoring_task.cancel()
        heartbeat_task.cancel()
        await report_completed(ctx, snap)
        await ws_logger.close()
        sim_log.info("Pipeline shut down")