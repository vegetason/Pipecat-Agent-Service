"""
utils/error_handler.py
----------------------
Custom exceptions and retry logic for the agent service.
Every external provider call (Deepgram, Claude, Cartesia, Daily) should
be wrapped with @retry so a transient network blip doesn't kill a simulation.
"""

import asyncio
import functools
from typing import Callable, Tuple, Type

from utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class AgentError(Exception):
    """Base exception for all agent errors."""


class ProviderError(AgentError):
    """External provider (Deepgram, Claude, Cartesia, Daily) failed."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")


class PipelineError(AgentError):
    """Pipecat pipeline failed to start or crashed mid-simulation."""


class SimulationError(AgentError):
    """Business logic error during a simulation (bad state, missing data)."""


class ConsentError(AgentError):
    """Feature requires consent the user hasn't given (e.g. Ghost Mode)."""


class ContextError(AgentError):
    """Simulation context payload is missing required fields."""


# ---------------------------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------------------------

def retry(
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Async retry with exponential backoff.

    Usage:
        @retry(attempts=3, delay=1.0, exceptions=(ProviderError,))
        async def call_deepgram(audio: bytes) -> str: ...

    Args:
        attempts:   Total number of tries before raising.
        delay:      Seconds to wait before the second attempt.
        backoff:    Multiplier applied to delay after each failure.
        exceptions: Only retry on these exception types.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == attempts:
                        log.error(
                            "All retry attempts exhausted",
                            func=func.__name__, attempts=attempts, error=str(exc),
                        )
                        raise
                    log.warning(
                        "Attempt failed, retrying",
                        func=func.__name__, attempt=attempt,
                        total=attempts, wait_seconds=wait, error=str(exc),
                    )
                    await asyncio.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator