"""
config/server.py
----------------
Config for the agent's own HTTP server and its connection to the Node.js backend.
"""

from dataclasses import dataclass, field
from config.helpers import require, optional, optional_int


@dataclass
class ServerConfig:
    host: str = field(default_factory=lambda: optional("AGENT_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: optional_int("AGENT_PORT", 8000))
    # How long to wait for a simulation context payload before timing out
    startup_timeout_seconds: int = field(
        default_factory=lambda: optional_int("STARTUP_TIMEOUT_SECONDS", 30)
    )


@dataclass
class NodeAPIConfig:
    base_url: str = field(default_factory=lambda: require("NODEJS_API_URL"))
    websocket_url: str = field(default_factory=lambda: require("NODEJS_WS_URL"))
    # Shared secret so Node.js can verify the agent's requests
    internal_secret: str = field(default_factory=lambda: require("INTERNAL_API_SECRET"))
    # How often (seconds) the agent sends a heartbeat to Node.js during a simulation
    heartbeat_interval: int = field(
        default_factory=lambda: optional_int("HEARTBEAT_INTERVAL_SECONDS", 5)
    )