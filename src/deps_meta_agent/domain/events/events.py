from dataclasses import dataclass

from deps_message_flow.events.common import DomainEvent

__all__ = ["TestEvent"]


@dataclass
class TestEvent(DomainEvent):
    test: str
