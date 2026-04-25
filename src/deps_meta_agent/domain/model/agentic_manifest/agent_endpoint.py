from ..shared import Guard, ImmutableCheck, ValueObject
from .types import RawAgentEndpoint

__all__ = ["AgentEndpoint"]


class AgentEndpoint(metaclass=ValueObject):
    url = Guard[str](str, ImmutableCheck())
    timeout = Guard[int](int, ImmutableCheck())

    def __init__(self, url: str, timeout: int) -> None:
        self.url = url
        self.timeout = timeout

    @classmethod
    def from_raw(cls, data: RawAgentEndpoint) -> "AgentEndpoint":
        return cls(
            url=data["url"],
            timeout=data["timeout"],
        )
