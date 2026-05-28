"""
modes/mode_config.py
-------------------
Mode-specific pipeline configuration.
Called by pipeline_builder to apply mode overrides
(silent, ghost, warmup, mirror) after core pipeline is built.
"""

from utils.logger import get_logger

log = get_logger(__name__)


async def apply_mode(ctx: dict, tts, speak, ws_emit) -> list[str]:
    """
    Apply mode-specific configuration. Returns a list of active mode names.
    Silent mode: disables TTS, emits questions to display layer.
    Ghost mode: generates ideal answers, synthesizes with voice clone.
    Warmup mode: swaps question bank with warmup questions.
    Mirror mode: flags for replay tracking (no pipeline change needed).
    """
    mode = ctx.get("mode", "full")
    active: list[str] = []

    if mode == "silent":
        from modes.silent_mode import configure_silent_pipeline
        await configure_silent_pipeline(tts, speak, ws_emit, ctx)
        active.append("silent")
    elif mode == "ghost":
        from modes.ghost_mode import generate_all_ideal_answers
        from utils.consent_manager import require_voice_clone
        profile = ctx.get("candidate_profile", {})
        voice_id = require_voice_clone(profile)
        answers = await generate_all_ideal_answers(ctx)
        log.info("Ghost Mode answers generated", count=len(answers))
        from services.voice_cloning import synthesize_ideal_answers
        texts = [a["ideal_answer"] for a in answers]
        audio_chunks = await synthesize_ideal_answers(voice_id, texts)
        log.info("Ghost Mode audio synthesized", chunks=len(audio_chunks))
        active.append("ghost")
    elif mode == "warmup":
        from modes.warmup_mode import warmup_questions, warmup_persona_prompt
        ctx["question_bank"] = warmup_questions()
        ctx["persona_override"] = warmup_persona_prompt()
        ctx["duration_minutes"] = 5
        active.append("warmup")
    elif mode == "mirror":
        ctx["mirror_mode"] = True
        active.append("mirror")

    return active
