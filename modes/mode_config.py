"""
modes/mode_config.py
-------------------
Mode-specific pipeline configuration.
Called by pipeline_builder to apply mode overrides before the pipeline runs.
Handles all 10 simulation modes from PRD §6.7.

Modes split into two categories:
  Context-only: nightmare, rapid_fire, mirror, warmup — override context dict,
                no pipeline changes needed.
  Pipeline-modifying: silent, ghost — disable/redirect TTS or add pre-gen step.
  Pass-through: full, drill, blind, endurance — configured entirely by Node.js
                via the question bank and context fields; agent runs normally.
"""

from utils.logger import get_logger

log = get_logger(__name__)


async def apply_mode(ctx: dict, tts, speak, ws_emit) -> list[str]:
    """
    Apply mode-specific overrides. Returns list of active mode names.
    Context overrides are applied first; pipeline changes second.
    """
    mode = ctx.get("mode", "full")
    active: list[str] = []

    # ── Context-only overrides ────────────────────────────────────────────
    if mode == "nightmare":
        from modes.nightmare_mode import apply_nightmare_overrides
        apply_nightmare_overrides(ctx)
        active.append("nightmare")

    elif mode == "rapid_fire":
        from modes.rapid_fire_mode import apply_rapid_fire_overrides
        apply_rapid_fire_overrides(ctx)
        active.append("rapid_fire")

    elif mode == "mirror":
        from modes.mirror_mode import apply_mirror_overrides
        apply_mirror_overrides(ctx)
        active.append("mirror")

    elif mode == "warmup":
        from modes.warmup_mode import warmup_questions, warmup_persona_prompt
        ctx["question_bank"] = warmup_questions()
        ctx["persona_override"] = warmup_persona_prompt()
        ctx["duration_minutes"] = 5
        active.append("warmup")

    # ── Pipeline-modifying modes ──────────────────────────────────────────
    elif mode == "silent":
        from modes.silent_mode import configure_silent_pipeline
        await configure_silent_pipeline(tts, speak, ws_emit, ctx)
        active.append("silent")

    elif mode == "ghost":
        from modes.ghost_mode import generate_all_ideal_answers
        from utils.consent_manager import require_voice_clone
        from services.voice_cloning import synthesize_ideal_answers
        profile = ctx.get("candidate_profile", {})
        voice_id = require_voice_clone(profile)
        answers = await generate_all_ideal_answers(ctx)
        texts = [a["ideal_answer"] for a in answers]
        audio_chunks = await synthesize_ideal_answers(voice_id, texts)
        log.info("Ghost Mode ready", answers=len(answers), audio=len(audio_chunks))
        active.append("ghost")

    # ── Pass-through modes (no agent-side changes needed) ─────────────────
    # full, drill, blind, endurance: question bank and duration fully
    # configured by Node.js before spawning the agent.
    elif mode in ("full", "drill", "blind", "endurance"):
        active.append(mode)

    else:
        log.warning("Unknown mode — running as full simulation", mode=mode)
        active.append("full")

    return active