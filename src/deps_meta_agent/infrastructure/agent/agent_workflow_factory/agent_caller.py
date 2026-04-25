import logging

from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.adapters import HttpAgentStreamClient, SSEEvent

from ..types import AgenticPayload

__all__ = ["AgentCaller"]


class AgentCaller:
    def __init__(self, agent_client: HttpAgentStreamClient) -> None:
        self._agent_client = agent_client
        self._logger = logging.getLogger(self.__class__.__name__)

    async def call_agent(
        self,
        manifest: AgenticManifest,
        payload: AgenticPayload,
    ) -> tuple[list[SSEEvent], str]:
        self._logger.info("Calling agent '%s' at %s", manifest.code, manifest.endpoint.url)

        events = []
        parts = []

        event_stream = self._agent_client.stream_chat(
            manifest=manifest,
            payload=payload,
        )

        async for event in event_stream:
            events.append(event)
            parts.append(event["text"])

        response_text = "".join(parts)
        self._logger.info("Agent '%s' responded with %d chars", manifest.code, len(response_text))

        return events, response_text
