from typing import Any, TypeAlias, TypedDict

__all__ = ["RawAgentArgument", "RawConversationTurn", "RawContextBundle", "ToolArgumentsMap"]


class RawAgentArgument(TypedDict):
    value: Any


class RawConversationTurn(TypedDict):
    question: str
    answer: str


class RawContextBundle(TypedDict):
    conversation_trim: list[RawConversationTurn]


ToolDateCode: TypeAlias = str
ToolArgumentsMap: TypeAlias = dict[ToolDateCode, list[RawAgentArgument]]
