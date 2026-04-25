from typing import TypedDict

from .raw_agent_endpoint import RawAgentEndpoint

__all__ = ["RawAgenticManifest"]


class RawAgenticManifest(TypedDict):
    code: str
    name: str
    description: str
    endpoint: RawAgentEndpoint
