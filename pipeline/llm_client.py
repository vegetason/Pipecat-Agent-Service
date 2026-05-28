"""
pipeline/llm_client.py
-----------------------
The speak() function — the bridge between the state machine and the pipeline.

When interview_flow.py calls speak(instruction), this module:
  1. Sends the instruction to Claude as a system prompt
  2. Gets the interviewer's response text back
  3. Pushes it into the TTS queue so Cartesia speaks it aloud

This is intentionally thin — all prompt assembly happens in context_builder.py.
"""

import asyncio
from anthropic import AsyncAnthropic

from config import config
from utils.logger import get_logger
from utils.error_handler import retry, ProviderError

log = get_logger(__name__)
_client = AsyncAnthropic(api_key=config.claude.api_key)


@retry(attempts=3, delay=1.0, exceptions=(ProviderError,))
async def ask_claude(system_prompt: str, simulation_id: str) -> str:
    """
    Send a system prompt to Claude and return the interviewer's spoken response.

    Args:
        system_prompt:  Full assembled prompt from context_builder.
        simulation_id:  For logging only.

    Returns:
        The text Claude generated — passed to TTS next.
    """
    log.debug("Calling Claude", simulation_id=simulation_id)
    try:
        response = await _client.messages.create(
            model=config.claude.model,
            max_tokens=config.claude.max_tokens,
            temperature=config.claude.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": "Proceed."}],
        )
        text = response.content[0].text.strip()
        log.debug("Claude responded", simulation_id=simulation_id, chars=len(text))
        return text
    except Exception as e:
        raise ProviderError("Claude", str(e))


def make_speak_fn(tts_queue: asyncio.Queue, simulation_id: str):
    """
    Returns the speak() coroutine that interview_flow.py calls.
    Closes over the TTS queue so the state machine never touches the pipeline directly.

    Args:
        tts_queue:     asyncio.Queue that pipeline_builder drains into Cartesia.
        simulation_id: For logging.
    """
    async def speak(instruction: str) -> None:
        text = await ask_claude(instruction, simulation_id)
        await tts_queue.put(text)
        log.info("Agent speech queued", simulation_id=simulation_id, preview=text[:60])

    return speak