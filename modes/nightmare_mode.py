"""
modes/nightmare_mode.py
-----------------------
Nightmare Mode — hardest persona, shortest effective time, most aggressive
follow-ups, Pressure Multiplier always on, nightmare difficulty.

PRD §6.7: "Hardest persona, shortest time, most aggressive follow-ups
+ Pressure Multiplier always on."

No pipeline changes needed — overrides are applied to the context dict
before the pipeline starts. context_builder.py reads difficulty and persona
to assemble the correct system prompt.
"""

from utils.logger import get_logger

log = get_logger(__name__)

# Nightmare allows one extra follow-up per question vs standard
_NIGHTMARE_MAX_FOLLOWUPS = 3

# Personas ranked by pressure — pick the harshest available
_NIGHTMARE_PERSONA_PRIORITY = ("devils_advocate", "silent_type", "big_tech_engineer")


def is_nightmare_mode(ctx: dict) -> bool:
    return ctx.get("mode") == "nightmare"


def apply_nightmare_overrides(ctx: dict) -> dict:
    """
    Inject nightmare-specific overrides into the simulation context.
    Called by mode_config.py before the pipeline is assembled.

    Overrides:
      - difficulty → "nightmare"  (section_builders appends "Be maximally unforgiving")
      - pressure_multiplier → True  (always escalates on strong answers)
      - weakness_memory → True  (proactively coaches on known weaknesses before start)
      - max_followups_per_question → 3  (one more than standard cap of 2)
      - persona → most aggressive available if not already a pressure persona
    """
    ctx["difficulty"] = "nightmare"
    ctx["pressure_multiplier"] = True
    ctx["weakness_memory"] = True
    ctx["max_followups_per_question"] = _NIGHTMARE_MAX_FOLLOWUPS

    current_persona = ctx.get("persona", "")
    if current_persona not in _NIGHTMARE_PERSONA_PRIORITY:
        ctx["persona"] = _NIGHTMARE_PERSONA_PRIORITY[0]

    log.info(
        "Nightmare mode overrides applied",
        simulation_id=ctx.get("simulation_id"),
        persona=ctx["persona"],
        difficulty=ctx["difficulty"],
    )
    return ctx