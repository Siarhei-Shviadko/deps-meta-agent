from enum import Enum
from typing import TypedDict

__all__ = ["SSEEvent", "SSEEventType"]


class SSEEventType(str, Enum):
    TOOL_CALL = "ToolCall"
    REASONING = "Reasoning"
    TOOL_CALL_RESPONSE = "ToolCallResponse"
    FINAL = "Final"

    @classmethod
    def from_string(cls, value: str) -> "SSEEventType | None":
        for event_type in cls:
            if event_type.value == value:
                return event_type
        return None


class SSEEvent(TypedDict):
    type: SSEEventType
    text: str
