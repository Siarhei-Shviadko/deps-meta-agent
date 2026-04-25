from typing import AsyncIterator, Protocol

from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.adapters import SSEEvent
from deps_meta_agent.infrastructure.agent import AgenticPayload

__all__ = ["AgentStreamClient"]


class AgentStreamClient(Protocol):
    async def stream_chat(
        self,
        manifest: AgenticManifest,
        payload: AgenticPayload,
    ) -> AsyncIterator[SSEEvent]:
        ...
