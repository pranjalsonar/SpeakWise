from enum import Enum


class SessionMode(str, Enum):
    RANDOM = "RANDOM"
    CUSTOM = "CUSTOM"
    DAILY = "DAILY"


class SessionStatus(str, Enum):
    CREATED = "CREATED"
    LEARNING = "LEARNING"
    READY_TO_RECORD = "READY_TO_RECORD"
    RECORDING = "RECORDING"
    PROCESSING = "PROCESSING"
    FEEDBACK_READY = "FEEDBACK_READY"
    COMPLETED = "COMPLETED"