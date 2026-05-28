"""
subagents/proctoring_rules.py
------------------------------
Pure flag detection functions for the proctoring agent.
Each function takes raw signal data and returns a flag dict or None.
No I/O, no async — easy to unit test in isolation.

Flag severity levels:
  "low"    — minor distraction, logged only
  "medium" — suspicious, shown in report
  "high"   — strong integrity concern, flagged prominently
"""

from dataclasses import dataclass


@dataclass
class ProctoringFlag:
    flag_type: str
    severity: str   # "low" | "medium" | "high"
    detail: str


def check_face_absence(face_count: int) -> ProctoringFlag | None:
    """No face detected in frame."""
    if face_count == 0:
        return ProctoringFlag(
            flag_type="face_absent",
            severity="high",
            detail="No face detected in camera frame.",
        )
    return None


def check_multiple_faces(face_count: int) -> ProctoringFlag | None:
    """More than one face in frame — possible third-party assistance."""
    if face_count > 1:
        return ProctoringFlag(
            flag_type="multiple_faces",
            severity="high",
            detail=f"{face_count} faces detected in frame.",
        )
    return None


def check_gaze_direction(gaze_x: float, gaze_y: float) -> ProctoringFlag | None:
    """
    Gaze significantly off-screen — reading notes or second monitor.
    gaze_x and gaze_y are normalized -1.0 to 1.0 (0,0 = looking at camera).
    """
    off_center = (gaze_x ** 2 + gaze_y ** 2) ** 0.5
    if off_center > 0.75:
        return ProctoringFlag(
            flag_type="gaze_off_screen",
            severity="medium",
            detail=f"Gaze deviation score: {off_center:.2f}",
        )
    return None


def check_background_noise(noise_db: float) -> ProctoringFlag | None:
    """Sudden loud background noise — possible coaching or conversation."""
    if noise_db > 65.0:
        return ProctoringFlag(
            flag_type="background_noise",
            severity="medium",
            detail=f"Background noise detected at {noise_db:.1f} dB.",
        )
    return None


def check_voice_consistency(
    current_pitch_hz: float,
    baseline_pitch_hz: float,
) -> ProctoringFlag | None:
    """
    Large pitch deviation from baseline — possible voice substitution.
    Baseline established in first 60 seconds of the simulation.
    """
    if baseline_pitch_hz == 0:
        return None
    deviation = abs(current_pitch_hz - baseline_pitch_hz) / baseline_pitch_hz
    if deviation > 0.35:
        return ProctoringFlag(
            flag_type="voice_inconsistency",
            severity="high",
            detail=f"Voice pitch deviated {deviation:.0%} from baseline.",
        )
    return None


