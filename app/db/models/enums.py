from enum import StrEnum


class GuestLanguage(StrEnum):
    ENGLISH = "en-IN"
    Hindi = "hi-IN"
    HINGLISH = "hi-en"
    TAMIL = "ta-IN"
    TELUGU = "te-IN"
    KANNADA = "kn-IN"
    MALAYALAM = "ml-IN"
    MARATHI = "mr-IN"
    BENGALI = "bn-IN"
    GUJARATI = "gu-IN"
    PUNJABI = "pa-IN"


class RequestCategory(StrEnum):
    HOUSEKEEPING = "HOUSEKEEPING"
    MAINTENANCE = "MAINTENANCE"
    FRONT_DESK = "FRONT_DESK"
    OTHER = "OTHER"


class RequestPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RequestStatus(StrEnum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
