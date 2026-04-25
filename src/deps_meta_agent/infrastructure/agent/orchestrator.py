import logging
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from langchain_core.runnables.config import RunnableConfig
from langgraph.errors import GraphRecursionError

from deps_meta_agent.domain.model import AgenticManifest

from .agent_workflow_factory import OrchestratorWorkflowFactory
from .response import OrchestratorChunk
from .session import Session
from .state import OrchestratorState
from .types import AgenticPayload, AgentResponse, ManifestInfo

__all__ = ["MetaAgentOrchestrator"]


class MetaAgentOrchestrator:  # noqa: WPS214
    _max_steps_for_single_request: int = 20
    _session_ttl_hours: int = 1

    def __init__(
        self,
        workflow_factory: OrchestratorWorkflowFactory,
    ) -> None:
        self._workflow_factory = workflow_factory
        self._sessions: dict[str, Session] = {}

        self._logger = logging.getLogger(self.__class__.__name__)

    async def stream(  # noqa: WPS231
        self,
        manifests: list[AgenticManifest],
        payload: AgenticPayload,
    ) -> AsyncGenerator[AgentResponse, None]:
        session: Session | None = None
        try:
            session = await self._get_or_create_session(
                conversation_id=payload.conversation_id,
                manifests=manifests,
            )

            state, workflow, config = self._prepare_workflow_execution(
                payload=payload,
                session=session,
            )

            final_state = None
            async for step_state in workflow.astream(state, stream_mode="values", config=config):
                final_state = step_state

                for event in self._collect_step_events(step_state):
                    yield event

            final_answer = self._extract_final_answer(final_state)

            if session and final_state:
                self._finalize_session(
                    session=session,
                    final_state=final_state,
                    question=payload.question,
                    answer=final_answer,
                )

            yield OrchestratorChunk.final(final_answer).to_sse_event()

        except Exception as exc:
            error_answer = self._handle_workflow_error(
                error=exc,
                session=session,
                question=payload.question,
            )
            yield OrchestratorChunk.final(error_answer).to_sse_event()

    def _get_session(self, conversation_id: str) -> Session | None:
        session = self._sessions.get(conversation_id)
        if session:
            session.last_accessed_at = datetime.now(timezone.utc)
        return session

    def _create_session(
        self,
        conversation_id: str,
        manifests: list[AgenticManifest],
    ) -> Session:
        session = Session(
            conversation_id=conversation_id,
            manifests=manifests,
        )
        self._sessions[conversation_id] = session
        self._logger.info("Created session for conversation '%s' with %d manifests", conversation_id, len(manifests))
        return session

    async def _cleanup_expired_sessions(self) -> None:
        now = datetime.now(timezone.utc)
        ttl_threshold = now - timedelta(hours=self._session_ttl_hours)

        expired_conversation_ids = [
            conversation_id
            for conversation_id, session in self._sessions.items()
            if session.last_accessed_at < ttl_threshold
        ]

        for conversation_id in expired_conversation_ids:
            session = self._sessions.pop(conversation_id, None)
            if session:
                self._logger.info("Removed expired session for conversation '%s'", conversation_id)

    async def _get_or_create_session(
        self,
        conversation_id: str,
        manifests: list[AgenticManifest],
    ) -> Session:
        await self._cleanup_expired_sessions()

        session = self._get_session(conversation_id)
        if session:
            session.update_manifests(manifests)

        else:
            session = self._create_session(
                conversation_id=conversation_id,
                manifests=manifests,
            )

        return session

    def _initialize_state(
        self,
        payload: AgenticPayload,
        available_manifests: list[ManifestInfo],
        session: Session,
    ) -> OrchestratorState:
        state = OrchestratorState.from_request(
            payload=payload,
            available_manifests=available_manifests,
            session=session,
        )

        self._logger.info(
            "Initialized orchestrator state for conversation '%s' " "(active_agent=%s)",
            payload.conversation_id,
            session.active_agent_code,
        )
        return state

    def _prepare_workflow_execution(
        self,
        payload: AgenticPayload,
        session: Session,
    ) -> tuple[OrchestratorState, Any, RunnableConfig]:
        manifest_infos = [ManifestInfo.from_manifest(m) for m in session.manifests]
        state = self._initialize_state(
            payload=payload,
            available_manifests=manifest_infos,
            session=session,
        )

        workflow = self._workflow_factory.create_workflow()
        config = RunnableConfig(recursion_limit=self._max_steps_for_single_request)

        self._logger.info(
            "Starting orchestration for conversation '%s' (active_agent=%s)",
            payload.conversation_id,
            session.active_agent_code,
        )

        return state, workflow, config

    def _collect_step_events(self, step_state: Any) -> list[AgentResponse]:
        events = []

        events.extend(self._get_new_agent_events(step_state))

        reasoning_event = self._get_evaluation_reasoning(step_state)
        if reasoning_event:
            events.append(reasoning_event)

        routing_event = self._check_agent_routing(step_state)
        if routing_event:
            events.append(routing_event)

        return events

    def _check_agent_routing(self, step_state: Any) -> AgentResponse | None:
        if not isinstance(step_state, dict):
            return None

        agent_code = step_state.get("current_agent_code")
        if not agent_code:
            return None

        attempted_agents = step_state.get("attempted_agents", [])
        previous_attempts = attempted_agents[:-1] if len(attempted_agents) > 1 else []
        if agent_code not in previous_attempts:
            reasoning_text = f"Routing to agent: {agent_code} - {step_state.get('current_agent_response', " ")}"
            return OrchestratorChunk.reasoning(reasoning_text).to_sse_event()

        return None

    def _get_new_agent_events(self, step_state: Any) -> list[AgentResponse]:
        if not isinstance(step_state, dict):
            return []

        current_agent_events = step_state.get("current_agent_events", [])
        emitted_count = step_state.get("_emitted_event_count", 0)

        new_events = current_agent_events[emitted_count:]

        if new_events:
            step_state["_emitted_event_count"] = len(current_agent_events)

        return new_events

    def _get_evaluation_reasoning(self, step_state: Any) -> AgentResponse | None:
        if not isinstance(step_state, dict):
            return None

        evaluation_reasoning = step_state.get("evaluation_reasoning")
        if not evaluation_reasoning:
            return None

        step_state["evaluation_reasoning"] = None

        return OrchestratorChunk.reasoning(evaluation_reasoning).to_sse_event()

    def _extract_final_answer(self, final_state: dict | None) -> str:
        if not final_state:
            return "Unable to generate a response."

        if final_answer := final_state.get("final_answer"):
            return final_answer

        return "Unable to generate a response."

    def _finalize_session(
        self,
        session: Session,
        final_state: dict | None,
        question: str,
        answer: str,
    ) -> None:
        session.add_conversation_turn(question, answer)

        if final_state and final_state.get("current_agent_code"):
            session.set_active_agent(final_state["current_agent_code"])
            self._logger.info(
                "Session '%s' active agent set to '%s'",
                session.conversation_id,
                final_state["current_agent_code"],
            )

    def _handle_workflow_error(
        self,
        error: Exception,
        session: Session | None,
        question: str,
    ) -> str:
        if isinstance(error, GraphRecursionError):
            error_answer = f"The orchestration workflow exceeded maximum iterations: {error}"
            self._logger.error("Graph recursion error: %s", error_answer, exc_info=True)
        else:
            error_answer = f"An unexpected error occurred: {str(error)}"
            self._logger.error(error_answer, exc_info=True)

        if session is not None:
            session.add_conversation_turn(question, error_answer)
            session.clear_active_agent()

        return error_answer
