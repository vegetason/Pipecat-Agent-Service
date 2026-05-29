"""
modes/mirror_mode.py
---------------------
Mirror Mode — same simulation repeated so the candidate can track improvement
on identical questions across sessions. PRD §6.7: "Track improvement on
identical questions."

No pipeline changes are needed. The agent runs the interview normally.
The mirror flag and original_simulation_id are stored in context so Node.js
can generate a side-by-side comparison report between sessions.

Node.js is responsible for:
  - Loading the original simulation's question bank verbatim
  - Storing this session linked to original_simulation_id
  - Generating the per-question improvement delta in the post-sim report
"""

from utils.logger import get_logger

log = get_logger(__name__)


def is_mirror_mode(ctx: dict) -> bool:
    return ctx.get("mode") == "mirror"


def apply_mirror_overrides(ctx: dict) -> dict:
    """
    Flag the session for replay-comparison tracking.
    Logs a warning if no original_simulation_id was provided —
    Node.js should always supply this when spawning a mirror session.
    """
    ctx["mirror_mode"] = True

    original_id = ctx.get("original_simulation_id")
    sim_id = ctx.get("simulation_id")

    if original_id:
        log.info(
            "Mirror mode active — linked to original session",
            simulation_id=sim_id,
            original_simulation_id=original_id,
        )
    else:
        log.warning(
            "Mirror mode active but original_simulation_id not provided — "
            "Node.js will not be able to generate a comparison report",
            simulation_id=sim_id,
        )

    return ctx