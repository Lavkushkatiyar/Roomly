import re

from app.schemas.enums import ConfirmationStatus

AFFIRMATIVE_PATTERNS = ("yes", "ok")

NEGATIVE_PATTERNS = ("no", "cancel", "don't")


def classify_confirmation(transcript: str) -> ConfirmationStatus:
    normalized = re.sub(r"[^\w\s']", "", transcript.lower()).strip()
    words = normalized.split()[0]

    if not words or len(words) >= 4:
        return ConfirmationStatus.UNCLEAR

    if words in AFFIRMATIVE_PATTERNS:
        return ConfirmationStatus.CONFIRMED

    if words in NEGATIVE_PATTERNS:
        return ConfirmationStatus.DECLINED

    return ConfirmationStatus.UNCLEAR
