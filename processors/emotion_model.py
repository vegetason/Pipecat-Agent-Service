"""
processors/emotion_model.py
----------------------------
Emotion model loading and audio inference.
Supports two backends: "silero" (fast, light) or "wav2vec2" (accurate, heavy).
Backend is set via EMOTION_MODEL_BACKEND in .env.

Returns:
    stress_level: float 0.0 - 1.0
    emotion_tag:  one of "calm" | "anxious" | "overconfident" | "confused" | "disengaged"
"""

import numpy as np
from dataclasses import dataclass
from config import config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class EmotionResult:
    stress_level: float
    emotion_tag: str


# Emotion tag thresholds — maps raw model output to named states
_TAG_RULES = [
    (0.7,  "anxious"),
    (0.55, "overconfident"),
    (0.4,  "disengaged"),
    (0.25, "confused"),
]


def _score_to_tag(stress: float, energy: float) -> str:
    """Map stress + energy scores to a named emotion tag."""
    if stress >= 0.7:
        return "anxious"
    if stress < 0.3 and energy > 0.6:
        return "overconfident"
    if stress < 0.3 and energy < 0.3:
        return "disengaged"
    if 0.3 <= stress < 0.5 and energy < 0.4:
        return "confused"
    return "calm"


def _run_silero(audio: np.ndarray, sample_rate: int) -> EmotionResult:
    """
    Silero-based inference. Uses RMS energy and zero-crossing rate
    as lightweight proxies for stress and vocal energy.
    Replace with a real Silero emotion model call when available.
    """
    rms = float(np.sqrt(np.mean(audio ** 2)))
    zcr = float(np.mean(np.abs(np.diff(np.sign(audio)))) / 2)
    stress = min(1.0, rms * 8.0)
    energy = min(1.0, zcr * 4.0)
    tag = _score_to_tag(stress, energy)
    return EmotionResult(stress_level=round(stress, 3), emotion_tag=tag)


def _run_wav2vec2(audio: np.ndarray, sample_rate: int) -> EmotionResult:
    """
    wav2vec2-based inference placeholder.
    Swap in: facebook/wav2vec2-large-xlsr-53-emotion or similar HF model.
    """
    try:
        from transformers import pipeline as hf_pipeline
        classifier = hf_pipeline("audio-classification", model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
        results = classifier({"array": audio, "sampling_rate": sample_rate})
        top = results[0]
        stress = top["score"] if top["label"] in ("fearful", "angry", "sad") else 1 - top["score"]
        tag = _score_to_tag(stress, 0.5)
        return EmotionResult(stress_level=round(stress, 3), emotion_tag=tag)
    except Exception as e:
        log.warning("wav2vec2 inference failed, falling back to silero", error=str(e))
        return _run_silero(audio, sample_rate)


def run_inference(audio: np.ndarray, sample_rate: int = 16000) -> EmotionResult:
    """
    Run emotion inference on a chunk of audio.
    Backend selected from config.emotion.model_backend.
    """
    if config.emotion.model_backend == "wav2vec2":
        return _run_wav2vec2(audio, sample_rate)
    return _run_silero(audio, sample_rate)