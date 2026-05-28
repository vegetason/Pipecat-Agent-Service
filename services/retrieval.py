"""
services/retrieval.py
--------------------
HTTP client that fetches data from the Node.js backend API.
All calls use the internal secret for service-to-service auth.
"""

import httpx
from config import config
from utils.logger import get_logger

log = get_logger(__name__)
_HEADERS = {'Authorization': f'Bearer {config.node_api.internal_secret}'}


async def _get(path: str) -> dict:
    url = f'{config.node_api.base_url}{path}'
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(url, headers=_HEADERS)
            r.raise_for_status()
            return r.json().get('data', {})
        except Exception as e:
            log.warning('Node.js API call failed', path=path, error=str(e))
            return {}


async def fetch_question_bank(simulation_id: str) -> list[dict]:
    data = await _get(f'/api/v1/simulations/{simulation_id}/questions')
    return data.get('questions', [])


async def fetch_candidate_profile(user_id: str) -> dict:
    return await _get(f'/api/v1/profile/{user_id}')


async def fetch_simulation_config(simulation_id: str) -> dict:
    return await _get(f'/api/v1/simulations/{simulation_id}')
