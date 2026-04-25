import logging
from typing import AsyncGenerator

from deps_meta_agent.domain.exceptions import ManifestNotFound
from deps_meta_agent.domain.model import AgenticManifest
from deps_meta_agent.infrastructure.adapters import (
    RawContextBundle,
    SSEEvent,
    ToolArgumentsMap,
)
from deps_meta_agent.infrastructure.agent import AgenticPayload, MetaAgentOrchestrator
from deps_meta_agent.infrastructure.unit_of_work import AbstractUnitOfWork

__all__ = ["ChatService"]


class ChatService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        orchestrator: MetaAgentOrchestrator,
    ) -> None:
        self._uow = unit_of_work
        self._orchestrator = orchestrator
        self._logger = logging.getLogger(self.__class__.__name__)

    def validate_chat_preconditions(self, active_tool_sets: set[str]) -> list[AgenticManifest]:
        if not active_tool_sets:
            self._logger.warning("No active tool sets provided")
            raise ManifestNotFound("No active tool sets specified")

        with self._uow:
            manifests = self._uow.agentic_manifest.find_manifests_by_codes(list(active_tool_sets))

        if not manifests:
            self._logger.error(
                "No manifests found for active tool sets: %s",
                active_tool_sets,
            )
            tool_sets_str = ", ".join(sorted(active_tool_sets))
            raise ManifestNotFound(f"No agents found for tool sets: {tool_sets_str}")

        return manifests

    async def stream_chat(
        self,
        conversation_id: str,
        user_question: str,
        turn_id: str,
        context_bundle: RawContextBundle,
        arguments: ToolArgumentsMap,
        manifests: list[AgenticManifest],
    ) -> AsyncGenerator[SSEEvent, None]:
        self._logger.info(
            "Starting chat stream: conversation=%s, turn=%s, manifests=%d",
            conversation_id,
            turn_id,
            len(manifests),
        )

        payload = AgenticPayload(
            conversation_id=conversation_id,
            turn_id=turn_id,
            question=user_question,
            arguments=arguments,
            context_bundle=context_bundle,
        )

        async for event in self._orchestrator.stream(manifests, payload):
            yield event

        self._logger.info(
            "Completed chat stream: conversation=%s, turn=%s",
            conversation_id,
            turn_id,
        )
