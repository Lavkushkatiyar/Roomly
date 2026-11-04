import re

from app.schemas.enums import ConfirmationStatus

AFFIRMATIVE_PATTERNS = (
    r"yes",
    r"yes that's correct",
    r"please do",
)

NEGATIVE_PATTERNS = (
    r"no",
    r"no cancel it",
)


def classify_confirmation(transcript: str) -> ConfirmationStatus:
    normalized = re.sub(r"[^\w\s']", "", transcript.lower()).strip()
    words = normalized.split()

    if not words or len(words) >= 4:
        return ConfirmationStatus.UNCLEAR

    if normalized in AFFIRMATIVE_PATTERNS:
        return ConfirmationStatus.CONFIRMED

    if normalized in NEGATIVE_PATTERNS:
        return ConfirmationStatus.DECLINED

    return ConfirmationStatus.UNCLEAR
