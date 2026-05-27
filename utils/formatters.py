"""
utils/formatters.py
-------------------
Log formatters. JSONFormatter for production, HumanFormatter for development.
Imported by utils/logger.py only — nothing else should touch these directly.
"""

import json
import logging
import traceback
from datetime import datetime, timezone

# Fields on every LogRecord that aren't "extra" fields we added
_RESERVED = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


class JSONFormatter(logging.Formatter):
    """Single-line JSON per log record. Used in production."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class HumanFormatter(logging.Formatter):
    """Colored human-readable output. Used in development."""

    _COLORS = {
        "DEBUG": "\033[36m", "INFO": "\033[32m",
        "WARNING": "\033[33m", "ERROR": "\033[31m", "CRITICAL": "\033[35m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self._COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:<8}{self._RESET}"
        name = f"\033[90m{record.name}\033[0m"
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in _RESERVED and not k.startswith("_")
        }
        extras_str = "  " + "  ".join(f"{k}={v}" for k, v in extras.items()) if extras else ""
        line = f"{time_str} | {level} | {name} | {record.getMessage()}{extras_str}"
        if record.exc_info:
            line += "\n" + "".join(traceback.format_exception(*record.exc_info))
        return line