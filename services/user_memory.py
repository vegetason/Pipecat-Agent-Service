"""
services/user_memory.py
-----------------------
Fetches and parses weakness patterns from the Node.js backend
before a simulation starts, so the agent can deliver personalized
coaching notes.
"""

import httpx
from config import config
from utils.logger import get_logger

log = get_logger(__name__)
_HEADERS = {"Authorization": f"Bearer {config.node_api.internal_secret}"}


async def fetch_weakness_patterns(user_id: str) -> list[dict]:
    url = f"{config.node_api.base_url}/api/v1/profile/{user_id}/weaknesses"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(url, headers=_HEADERS)
            r.raise_for_status()
            patterns = r.json().get("data", {}).get("patterns", [])
            log.info("Weakness patterns fetched", user_id=user_id, count=len(patterns))
            return patterns
        except Exception as e:
            log.warning("Weakness fetch failed", user_id=user_id, error=str(e))
            return []


async def post_weakness_update(user_id: str, pattern_type: str) -> None:
    """Record a new instance of a weakness pattern occurrence."""
    url = f"{config.node_api.base_url}/api/v1/profile/{user_id}/weaknesses"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, headers=_HEADERS, json={"pattern_type": pattern_type})
        except Exception as e:
            log.debug("Weakness update skipped", error=str(e))
