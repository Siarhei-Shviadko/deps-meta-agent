from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel, ConfigDict, Field

from deps_meta_agent.infrastructure.adapters.types import (
    RawContextBundle,
    SSEEvent,
    ToolArgumentsMap,
)

from .session import Session
from .types import AgenticPayload, ManifestInfo

__all__ = ["OrchestratorState"]


class OrchestratorState(BaseModel):  # use specific parent
    model_config = ConfigDict(arbitrary_types_allowed=True)

    conversation_id: str
    turn_id: str
    question: str
    context_bundle: RawContextBundle
    arguments: ToolArgumentsMap
    attempted_agents: list[str] = []
    current_agent_code: str | None = None
    current_agent_response: str = ""
    final_answer: str | None = None
    iteration_count: int = 0
    available_manifests: list[ManifestInfo] = []
    messages: list[BaseMessage] = Field(default_factory=list)
    session: Session = Field(exclude=True)
    current_agent_events: list[SSEEvent] = Field(default_factory=list)
    evaluation_reasoning: str | None = None
    _emitted_event_count: int = 0

    @classmethod
    def from_request(
        cls,
        payload: AgenticPayload,
        available_manifests: list[ManifestInfo],
        session: Session,
    ) -> "OrchestratorState":
        return cls(
            conversation_id=payload.conversation_id,
            turn_id=payload.turn_id,
            question=payload.question,
            context_bundle=payload.context_bundle,
            arguments=payload.arguments,
            available_manifests=available_manifests,
            messages=[HumanMessage(content=payload.question)],
            session=session,
        )
