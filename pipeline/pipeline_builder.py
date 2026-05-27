"""
pipeline/pipeline_builder.py
-----------------------------
Stub — build_and_run will be fully implemented in the next step.
This lets main.py boot and complete the /start flow while we build
the real pipeline incrementally.
"""

import asyncio
from utils.logger import get_logger

log = get_logger(__name__)


async def build_and_run(ctx: dict) -> None:
    sim_log = log.bind(simulation_id=ctx["simulation_id"])
    sim_log.info("Pipeline stub — real pipeline coming next")
    # Simulate a short session so we can confirm the full flow works
    await asyncio.sleep(2)
    sim_log.info("Pipeline stub finished")