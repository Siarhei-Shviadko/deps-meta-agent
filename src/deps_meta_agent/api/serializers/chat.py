from typing import Any

from pydantic import Field

from deps_meta_agent.infrastructure.adapters.types import (
    RawAgentArgument,
    RawContextBundle,
    RawConversationTurn,
    SSEEventType,
    ToolArgumentsMap,
)

from .base import ConfiguredBaseModel

__all__ = ["ChatRequest", "SSEEventSerializer"]


class Argument(ConfiguredBaseModel):
    value: Any

    def to_dict(self) -> RawAgentArgument:
        return {
            "value": self.value,
        }


class ConversationTurn(ConfiguredBaseModel):
    question: str
    answer: str

    def to_dict(self) -> RawConversationTurn:
        return {
            "question": self.question,
            "answer": self.answer,
        }


class ContextBundle(ConfiguredBaseModel):
    conversation_trim: list[ConversationTurn] = Field(default_factory=list, alias="conversationTrim")

    def to_dict(self) -> RawContextBundle:
        return {"conversation_trim": [turn.to_dict() for turn in self.conversation_trim]}


class ChatRequest(ConfiguredBaseModel):
    conversation_id: str = Field(..., alias="conversationId")
    turn_id: str = Field(..., alias="turnId")
    user_question: str = Field(..., alias="userQuestion")
    active_tool_sets: list[str] = Field(..., alias="activeToolSets")
    context_bundle: ContextBundle = Field(default_factory=ContextBundle, alias="contextBundle")
    arguments: dict[str, list[Argument]] = Field(default_factory=dict)

    def raw_arguments(self) -> ToolArgumentsMap:
        return {key: [arg.to_dict() for arg in value] for key, value in self.arguments.items()}

    def raw_context_bundle(self) -> RawContextBundle:
        return self.context_bundle.to_dict()


class SSEEventSerializer(ConfiguredBaseModel):
    type: SSEEventType
    text: str

    def to_dict(self) -> dict[str, str]:
        return {
            "type": self.type,
            "text": self.text,
        }
