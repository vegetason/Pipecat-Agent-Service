"""
config/helpers.py
-----------------
Shared env-loading helpers used by every config section file.
Import these instead of calling os.getenv() anywhere else in the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def require(key: str) -> str:
    """
    Load a required env var.
    Crashes immediately at startup with a clear message if the key is missing.
    Use this for API keys, URLs and anything the agent cannot run without.
    """
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Check your .env file."
        )
    return value


def optional(key: str, default: str = "") -> str:
    """
    Load an optional env var, returning a default if not set.
    Use this for tunable values (thresholds, timeouts, feature flags).
    """
    return os.getenv(key, default)


def optional_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def optional_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def optional_bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() == "true"