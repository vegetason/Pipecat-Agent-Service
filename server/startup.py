"""
server/startup.py
----------------
App lifecycle, dev fixture loading, and context validation.
Extracted from main.py to keep it under 100 lines.
"""

import json
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import config
from utils.logger import get_logger
from utils.error_handler import ContextError

log = get_logger(__name__)

_REQUIRED_FIELDS = ["simulation_id", "room_url", "persona", "mode", "question_bank"]


def make_lifespan() -> callable:
    """Returns the FastAPI lifespan context manager."""
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info(
            "Intervue agent service starting",
            env=config.env, host=config.server.host, port=config.server.port,
        )
        yield
        log.info("Intervue agent service shut down")
    return lifespan


def load_dev_fixture() -> dict:
    """Load simulation context from a local JSON file during development."""
    filepath = "dev_fixtures/simulation_context.json"
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Dev fixture not found at '{filepath}'. "
            "Copy dev_fixtures/simulation_context.example.json and fill it in."
        )
    with open(filepath) as f:
        return json.load(f)


def validate_context(ctx: dict) -> None:
    """Raise ContextError if any required field is missing."""
    missing = [f for f in _REQUIRED_FIELDS if f not in ctx]
    if missing:
        raise ContextError(f"Simulation context missing required fields: {missing}")
