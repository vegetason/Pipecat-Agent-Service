"""
pipeline/llm_client.py
-----------------------
The speak() function — the bridge between the state machine and the pipeline.

When interview_flow.py calls speak(instruction), this module:
  1. Sends the instruction to Groq as a system prompt
  2. Gets the interviewer's response text back
  3. Pushes it into the TTS queue so Cartesia speaks it aloud

This is intentionally thin — all prompt assembly happens in context_builder.py.
"""

import asyncio
from groq import AsyncGroq

from config import config
from utils.logger import get_logger
from utils.error_handler import retry, ProviderError

log = get_logger(__name__)
_client = AsyncGroq(api_key=config.groq.api_key)


@retry(attempts=3, delay=1.0, exceptions=(ProviderError,))
async def ask_groq(system_prompt: str, simulation_id: str) -> str:
    """
    Send a system prompt to Groq and return the interviewer's spoken response.

    Args:
        system_prompt:  Full assembled prompt from context_builder.
        simulation_id:  For logging only.

    Returns:
        The text Groq generated — passed to TTS next.
    """
    log.debug("Calling Groq", simulation_id=simulation_id)
    try:
        response = await _client.chat.completions.create(
            model=config.groq.model,
            max_tokens=config.groq.max_tokens,
            temperature=config.groq.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Proceed."},
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        log.debug("Groq responded", simulation_id=simulation_id, chars=len(text))
        return text
    except Exception as e:
        raise ProviderError("Groq", str(e))


def make_speak_fn(tts_queue: asyncio.Queue, simulation_id: str):
    """
    Returns the speak() coroutine that interview_flow.py calls.
    Closes over the TTS queue so the state machine never touches the pipeline directly.

    Args:
        tts_queue:     asyncio.Queue that pipeline_builder drains into Cartesia.
        simulation_id: For logging.
    """
    async def speak(instruction: str) -> None:
        text = await ask_groq(instruction, simulation_id)
        await tts_queue.put(text)
        log.info("Agent speech queued", simulation_id=simulation_id, preview=text[:60])

    return speak
