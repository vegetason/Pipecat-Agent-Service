"""
main.py
-------
Entry point for the Intervue AI Pipecat agent service.

Node.js calls POST /start with the simulation context to boot a simulation.
The pipeline runs as a background asyncio task so this endpoint returns immediately.

In development, POST /start ignores the request body and loads from
dev_fixtures/simulation_context.json instead — so you can test without Node.js.
"""

import asyncio
import json
import os

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from config import config
from utils.logger import get_logger, setup_logging
from utils.error_handler import ContextError

setup_logging(config.env)
log = get_logger(__name__)

# Required fields every simulation context payload must contain
_REQUIRED_FIELDS = ["simulation_id", "room_url", "persona", "mode", "question_bank"]


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        "Intervue agent service starting",
        env=config.env, host=config.server.host, port=config.server.port,
    )
    yield
    log.info("Intervue agent service shut down")


app = FastAPI(title="Intervue Agent Service", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Dev fixture loader
# ---------------------------------------------------------------------------

def _load_dev_fixture() -> dict:
    """Load simulation context from a local JSON file during development."""
    path = "dev_fixtures/simulation_context.json"
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dev fixture not found at '{path}'. "
            "Copy dev_fixtures/simulation_context.example.json and fill it in."
        )
    with open(path) as f:
        return json.load(f)


def _validate_context(ctx: dict) -> None:
    missing = [f for f in _REQUIRED_FIELDS if f not in ctx]
    if missing:
        raise ContextError(f"Simulation context missing required fields: {missing}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Liveness check called by Node.js and Docker health checks."""
    return {"status": "ok", "env": config.env}


@app.post("/start")
async def start_simulation(request: Request):
    """
    Boot a simulation. Called by Node.js when a user starts an interview.
    Validates the context, then runs the pipeline as a background task.
    Returns immediately — the simulation runs asynchronously.
    """
    ctx = _load_dev_fixture() if config.is_dev else await request.json()

    try:
        _validate_context(ctx)
    except ContextError as e:
        raise HTTPException(status_code=422, detail=str(e))

    sim_log = log.bind(simulation_id=ctx["simulation_id"], persona=ctx["persona"])
    sim_log.info("Simulation start received", mode=ctx["mode"])

    # Import here to avoid loading heavy ML models at module import time
    from pipeline.pipeline_builder import build_and_run
    asyncio.create_task(build_and_run(ctx))

    return JSONResponse({"status": "started", "simulation_id": ctx["simulation_id"]})


@app.post("/end")
async def end_simulation(request: Request):
    """
    Graceful shutdown signal from Node.js (e.g. user disconnected mid-sim).
    The running pipeline task listens for this via a shared event.
    """
    body = await request.json()
    sim_id = body.get("simulation_id", "unknown")
    log.info("Simulation end requested", simulation_id=sim_id)
    # TODO: signal the running pipeline task to stop cleanly
    # (implemented in pipeline_builder.py)
    return JSONResponse({"status": "ending", "simulation_id": sim_id})


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.is_dev,
    )