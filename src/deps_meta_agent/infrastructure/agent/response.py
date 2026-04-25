from deps_meta_agent.infrastructure.adapters.types import SSEEvent, SSEEventType

__all__ = ["OrchestratorChunk"]


class OrchestratorChunk:
    def __init__(self, event_type: SSEEventType, text: str) -> None:
        self.event_type = event_type
        self.text = text

    @classmethod
    def from_sse_event(cls, event: SSEEvent) -> "OrchestratorChunk":
        return cls(
            event_type=event["type"],
            text=event["text"],
        )

    def to_sse_event(self) -> SSEEvent:
        return SSEEvent(type=self.event_type, text=self.text)

    @classmethod
    def reasoning(cls, text: str) -> "OrchestratorChunk":
        return cls(event_type=SSEEventType.REASONING, text=text)

    @classmethod
    def final(cls, text: str) -> "OrchestratorChunk":
        return cls(event_type=SSEEventType.FINAL, text=text)
