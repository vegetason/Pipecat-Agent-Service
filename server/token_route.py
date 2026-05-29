"""
server/token_route.py
---------------------
GET /participant-token — generates a LiveKit JWT for a browser participant.
Used by agent.html so the browser can join the same room as the agent.
Dev-only convenience endpoint — add auth before exposing in production.
"""

import time
import jwt
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse

from config import config
from utils.logger import get_logger

log = get_logger(__name__)


async def participant_token(
    room: str = Query(..., description="LiveKit room name"),
    identity: str = Query("candidate", description="Participant identity label"),
) -> JSONResponse:
    """Generate a LiveKit access token for a browser participant."""
    if not config.livekit.api_key or not config.livekit.api_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set "
                "to generate participant tokens."
            ),
        )

    now = int(time.time())
    claims = {
        "iss": config.livekit.api_key,
        "sub": identity,
        "nbf": now,
        "exp": now + 3600,
        "video": {
            "room": room,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
    }
    token = jwt.encode(claims, config.livekit.api_secret, algorithm="HS256")
    log.info("Participant token issued", room=room, identity=identity)

    return JSONResponse({
        "token": token,
        "url": config.livekit.url,
        "room": room,
        "identity": identity,
    })