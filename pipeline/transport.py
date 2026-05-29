"""
pipeline/transport.py
---------------------
Creates and configures the LiveKit WebRTC transport.
LiveKit is what puts the agent inside the room with the candidate.
"""

import time

import jwt

from pipecat.transports.livekit.transport import LiveKitParams, LiveKitTransport

from config import config
from utils.logger import get_logger

log = get_logger(__name__)


def _make_livekit_token(room_name: str, identity: str) -> str:
    """Create a LiveKit access token when the payload does not provide one."""
    if not config.livekit.api_key or not config.livekit.api_secret:
        raise ValueError(
            "livekit_token is required unless LIVEKIT_API_KEY and "
            "LIVEKIT_API_SECRET are set."
        )

    now = int(time.time())
    claims = {
        "iss": config.livekit.api_key,
        "sub": identity,
        "nbf": now,
        "exp": now + 60 * 60,
        "video": {
            "room": room_name,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
    }
    return jwt.encode(claims, config.livekit.api_secret, algorithm="HS256")


def create_transport(ctx: dict) -> LiveKitTransport:
    """
    Create a LiveKit transport for a simulation session.

    Required context:
      - livekit_url: LiveKit server URL, for example wss://project.livekit.cloud
      - livekit_room: room name
      - livekit_token: optional bot token. If omitted, env API key/secret are used.
    """
    sim_id = ctx["simulation_id"]
    livekit_url = ctx.get("livekit_url") or config.livekit.url
    room_name = ctx["livekit_room"]
    identity = ctx.get("livekit_identity") or f"{config.livekit.bot_identity}-{sim_id}"
    token = ctx.get("livekit_token") or _make_livekit_token(room_name, identity)

    if not livekit_url:
        raise ValueError("livekit_url is required in the /start payload or LIVEKIT_URL env var.")

    log.info(
        "Creating LiveKit transport",
        simulation_id=sim_id,
        livekit_url=livekit_url,
        room_name=room_name,
        identity=identity,
    )

    params = LiveKitParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        video_in_enabled=False,
        video_out_enabled=False,
    )

    transport = LiveKitTransport(
        url=livekit_url,
        token=token,
        room_name=room_name,
        params=params,
    )

    log.info("LiveKit transport created", simulation_id=sim_id)
    return transport
