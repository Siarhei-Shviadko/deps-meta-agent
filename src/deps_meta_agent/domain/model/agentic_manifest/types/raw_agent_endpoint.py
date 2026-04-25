from typing import TypedDict

__all__ = ["RawAgentEndpoint"]


class RawAgentEndpoint(TypedDict):
    url: str
    timeout: int
