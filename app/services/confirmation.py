import re

from app.schemas.enums import ConfirmationStatus

AFFIRMATIVE_PATTERNS = ("yes", "ok")

NEGATIVE_PATTERNS = ("no", "cancel", "don't")


def classify_confirmation(transcript: str) -> ConfirmationStatus:
    normalized = re.sub(r"[^\w\s']", "", transcript.lower()).strip()
    words = normalized.split()

    if not words or len(words) >= 4:
        return ConfirmationStatus.UNCLEAR

    first_word = words[0]

    if first_word in AFFIRMATIVE_PATTERNS or normalized == "please do":
        return ConfirmationStatus.CONFIRMED

    if first_word in NEGATIVE_PATTERNS:
        return ConfirmationStatus.DECLINED

    return ConfirmationStatus.UNCLEAR
