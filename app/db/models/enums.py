from enum import StrEnum


class GuestLanguage(StrEnum):
    ENGLISH = "en-IN"
    Hindi = "hi-IN"


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
