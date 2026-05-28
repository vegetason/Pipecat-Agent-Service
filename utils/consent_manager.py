"""
utils/consent_manager.py
-----------------------
Manages explicit user consent for features requiring permission,
particularly Ghost Mode voice cloning (ElevenLabs Voice Lab).
Consent is captured during onboarding and checked before every use.
"""

from utils.logger import get_logger
from utils.error_handler import ConsentError

log = get_logger(__name__)


def check_ghost_mode_consent(candidate_profile: dict) -> None:
    """
    Verify the candidate has explicitly consented to voice cloning.
    Raises ConsentError if consent is missing or revoked.
    """
    has_consent = candidate_profile.get("ghost_mode_consent", False)
    if not has_consent:
        raise ConsentError(
            "Ghost Mode requires explicit voice cloning consent. "
            "Consent must be granted during onboarding before this feature can be used."
        )
    log.info("Ghost Mode consent verified")


def has_voice_clone(candidate_profile: dict) -> bool:
    """Check if a voice clone ID already exists for this candidate."""
    clone_id = candidate_profile.get("voice_clone_id")
    return bool(clone_id and clone_id != "null" and clone_id is not None)


def require_voice_clone(candidate_profile: dict) -> str:
    """
    Verify consent and return the voice clone ID.
    Raises ConsentError if no clone exists.
    """
    check_ghost_mode_consent(candidate_profile)
    clone_id = candidate_profile.get("voice_clone_id")
    if not clone_id or clone_id == "null":
        raise ConsentError(
            "No voice clone found for this candidate. "
            "A voice clone must be created before Ghost Mode can be used."
        )
    return clone_id
