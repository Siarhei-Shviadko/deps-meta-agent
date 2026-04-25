from typing import TypeAlias

from pydantic import BaseModel

from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.adapters.types import (
    RawContextBundle,
    SSEEvent,
    ToolArgumentsMap,
)

__all__ = ["ManifestInfo", "AgenticPayload", "AgentResponse"]


class ManifestInfo(BaseModel):
    code: str
    name: str
    description: str
    endpoint_url: str
    timeout: int

    @classmethod
    def from_manifest(cls, manifest: AgenticManifest) -> "ManifestInfo":
        return cls(
            code=manifest.code,
            name=manifest.name,
            description=manifest.description,
            endpoint_url=manifest.endpoint.url,
            timeout=manifest.endpoint.timeout,
        )


class AgenticPayload(BaseModel):
    conversation_id: str
    turn_id: str
    question: str
    arguments: ToolArgumentsMap
    context_bundle: RawContextBundle


AgentResponse: TypeAlias = SSEEvent
