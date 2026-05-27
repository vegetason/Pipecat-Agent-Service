"""
utils/logger.py
---------------
Public API for logging across the entire agent service.
Import get_logger() in every module. Call setup_logging() once in main.py.

    from utils.logger import get_logger
    log = get_logger(__name__)
    log = log.bind(simulation_id="abc-123")
    log.info("Pipeline started", persona="corporate_executive")
"""

import logging
import sys
from utils.formatters import JSONFormatter, HumanFormatter
from utils.log_adapter import SimulationLogger

_configured = False


def setup_logging(env: str = "development") -> None:
    """Call once at startup in main.py before anything else runs."""
    global _configured
    if _configured:
        return
    use_json = env == "production"
    level = logging.DEBUG if env == "development" else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter() if use_json else HumanFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "asyncio", "daily"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> SimulationLogger:
    """
    Get a structured logger for a module. Always pass __name__.
    Returns a SimulationLogger with no context yet.
    Call .bind(simulation_id=...) once you have simulation context.
    """
    return SimulationLogger(logging.getLogger(name), {})