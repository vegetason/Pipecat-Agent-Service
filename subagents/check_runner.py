"""
subagents/check_runner.py
------------------------
Runs all proctoring checks against a signal snapshot.
Extracted from subagents/proctoring_rules.py.
"""

from subagents.proctoring_rules import (
    ProctoringFlag,
    check_face_absence,
    check_multiple_faces,
    check_gaze_direction,
    check_background_noise,
    check_voice_consistency,
)


def run_all_checks(signal: dict) -> list[ProctoringFlag]:
    """Run every check against a signal snapshot. Returns all flags found."""
    checks = [
        check_face_absence(signal.get("face_count", 1)),
        check_multiple_faces(signal.get("face_count", 1)),
        check_gaze_direction(signal.get("gaze_x", 0.0), signal.get("gaze_y", 0.0)),
        check_background_noise(signal.get("noise_db", 0.0)),
        check_voice_consistency(
            signal.get("current_pitch_hz", 0.0),
            signal.get("baseline_pitch_hz", 0.0),
        ),
    ]
    return [f for f in checks if f is not None]
