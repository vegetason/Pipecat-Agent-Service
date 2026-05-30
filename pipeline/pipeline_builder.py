"""
pipeline/pipeline_builder.py
-----------------------------
Assembles and runs the full Pipecat pipeline for one simulation session.
Processor creation → processor_factory.py | Background tasks → background_tasks.py
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
from pipeline.transcript_router import TranscriptRouter
from pipeline.background_tasks import start_background_tasks
from pipeline.speaking_gate import SpeakingGate
from pipeline.session_events import register_session_events
from state_machine.interview_flow import run_interview
from state_machine.states import InterviewState, SessionSnapshot
from services.transcript_logger import TranscriptLogger, make_ws_emit
from services.session_reporter import report_completed
from modes.mode_config import apply_mode
from utils.logger import get_logger
from utils.error_handler import PipelineError

log = get_logger(__name__)


async def build_and_run(ctx: dict) -> None:
    """Assemble and run the full interview pipeline for one simulation."""
    sim_id = ctx["simulation_id"]
    sim_log = log.bind(simulation_id=sim_id)
    stt, tts, vad = create_stt(sim_id), create_tts(sim_id), create_vad(sim_id)
    transport = create_transport(ctx, vad_analyzer=vad)

    ws_logger = TranscriptLogger(sim_id)
    await ws_logger.connect()
    ws_emit = make_ws_emit(ws_logger)

    tts_queue: asyncio.Queue[str] = asyncio.Queue()
    snap = SessionSnapshot(simulation_id=sim_id)
    gate = SpeakingGate()
    participant_joined = asyncio.Event()
    speak = make_speak_fn(tts_queue, sim_id, gate)

    if ctx.get("weakness_memory") and ctx.get("user_id"):
        from services.user_memory import fetch_weakness_patterns
        ctx["weakness_patterns"] = await fetch_weakness_patterns(ctx["user_id"])

    active_modes = await apply_mode(ctx, tts, speak, ws_emit)

    emotion, rambling, silence, _ = create_processors(sim_id, ctx, snap, speak, ws_emit)
    on_candidate_speech = make_on_candidate_speech(ctx, snap, speak, ws_emit)

    router = TranscriptRouter(sim_id, snap, on_candidate_speech, ws_emit)
    runner = PipelineRunner()
    register_session_events(transport, snap, runner, sim_log, gate, participant_joined)

    pipeline = Pipeline([
        transport.input(),
        stt,
        router,
        emotion,
        rambling,
        silence,
        tts,
        transport.output(),
    ])
    task = PipelineTask(pipeline)

    stop_event = asyncio.Event()
    proctoring_task, heartbeat_task = start_background_tasks(sim_id, ws_emit, stop_event)

    sim_log.info("Pipeline ready — waiting for candidate")
    try:
        await asyncio.gather(
            runner.run(task),
            run_interview(ctx, speak, snap, participant_joined),
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
