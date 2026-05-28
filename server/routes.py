"""
server/routes.py
---------------
FastAPI route handlers for the agent service.
Extracted from main.py to keep it under 100 lines.
"""

import asyncio

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from config import config
from server.startup import load_dev_fixture, validate_context
from utils.logger import get_logger
from utils.error_handler import ContextError

log = get_logger(__name__)


async def health():
    """Liveness check called by Node.js and Docker health checks."""
    return {"status": "ok", "env": config.env}


async def start_simulation(request: Request):
    """
    Boot a simulation. Called by Node.js when a user starts an interview.
    Validates the context, then runs the pipeline as a background task.
    """
    ctx = load_dev_fixture() if config.is_dev else await request.json()

    try:
        validate_context(ctx)
    except ContextError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sim_log = log.bind(simulation_id=ctx["simulation_id"], persona=ctx["persona"])
    sim_log.info("Simulation start received", mode=ctx["mode"])

    from pipeline.pipeline_builder import build_and_run
    asyncio.create_task(build_and_run(ctx))

    return JSONResponse({"status": "started", "simulation_id": ctx["simulation_id"]})


async def end_simulation(request: Request):
    """Graceful shutdown signal from Node.js."""
    body = await request.json()
    sim_id = body.get("simulation_id", "unknown")
    log.info("Simulation end requested", simulation_id=sim_id)
    return JSONResponse({"status": "ending", "simulation_id": sim_id})
