from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from deps_meta_agent.application.chat_service import ChatService
from deps_meta_agent.domain.exceptions import ManifestNotFound
from deps_meta_agent.infrastructure.adapters.types import (
    RawContextBundle,
    SSEEventType,
    ToolArgumentsMap,
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.__exit__.return_value = None
    return uow


@pytest.fixture
def mock_orchestrator():
    return Mock()


@pytest.fixture
def chat_service(mock_uow, mock_orchestrator):
    return ChatService(
        unit_of_work=mock_uow,
        orchestrator=mock_orchestrator,
    )


@pytest.fixture
def test_manifests(test_agentic_manifest_1, test_agentic_manifest_2):
    return [test_agentic_manifest_1, test_agentic_manifest_2]


def test_validate_chat_preconditions_successful(chat_service, mock_uow, test_manifests):
    active_tool_sets = {test_manifests[0].code, test_manifests[1].code}
    mock_uow.agentic_manifest.find_manifests_by_codes.return_value = test_manifests

    result = chat_service.validate_chat_preconditions(active_tool_sets)

    assert result == test_manifests
    mock_uow.__enter__.assert_called_once()
    mock_uow.agentic_manifest.find_manifests_by_codes.assert_called_once_with(list(active_tool_sets))
    mock_uow.__exit__.assert_called_once()


def test_validate_chat_preconditions_raises_when_no_manifests(chat_service, mock_uow):
    active_tool_sets = {"non-existent-tool"}
    mock_uow.agentic_manifest.find_manifests_by_codes.return_value = []

    with pytest.raises(ManifestNotFound) as exc_info:
        chat_service.validate_chat_preconditions(active_tool_sets)

    assert "non-existent-tool" in str(exc_info.value)
    mock_uow.__enter__.assert_called_once()
    mock_uow.agentic_manifest.find_manifests_by_codes.assert_called_once_with(list(active_tool_sets))
    mock_uow.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_stream_chat_successful_with_manifests(
    chat_service,
    mock_orchestrator,
    test_manifests,
):
    context_bundle: RawContextBundle = {"conversation_trim": []}
    arguments: ToolArgumentsMap = {}

    events = [
        {"type": SSEEventType.REASONING, "text": "Thinking..."},
        {"type": SSEEventType.TOOL_CALL, "text": "Calling tool"},
        {"type": SSEEventType.FINAL, "text": "Final answer"},
    ]

    async def stream_events():
        for event in events:
            yield event

    mock_orchestrator.stream = stream_events

    result_events = []
    async for event in chat_service.stream_chat(
        conversation_id="conv-123",
        user_question="test question",
        turn_id="comp-123",
        context_bundle=context_bundle,
        arguments=arguments,
        manifests=test_manifests,
    ):
        result_events.append(event)

    assert len(result_events) == 3
    assert result_events == events

    mock_orchestrator.stream.assert_called_once()
    call_args = mock_orchestrator.stream.call_args
    assert call_args[0][0] == test_manifests
    payload = call_args[0][1]
    assert payload.conversation_id == "conv-123"
    assert payload.turn_id == "comp-123"
    assert payload.question == "test question"
    assert payload.context_bundle == context_bundle
    assert payload.arguments == arguments


@pytest.mark.asyncio
async def test_stream_chat_passes_correct_parameters_to_orchestrator(
    chat_service,
    mock_orchestrator,
    test_manifests,
):
    context_bundle: RawContextBundle = {"conversation_trim": []}
    arguments: ToolArgumentsMap = {"tool1": [{"value": "test_arg"}]}

    async def stream_events():
        yield {"type": SSEEventType.FINAL, "text": "Done"}

    mock_orchestrator.stream = stream_events

    async for _ in chat_service.stream_chat(
        conversation_id="test-conv-id",
        user_question="What is the answer?",
        turn_id="test-completion-id",
        context_bundle=context_bundle,
        arguments=arguments,
        manifests=[test_manifests[0]],
    ):
        pass

    mock_orchestrator.stream.assert_called_once()
    call_args = mock_orchestrator.stream.call_args
    assert call_args[0][0] == [test_manifests[0]]

    payload = call_args[0][1]
    assert payload.conversation_id == "test-conv-id"
    assert payload.turn_id == "test-completion-id"
    assert payload.question == "What is the answer?"
    assert payload.context_bundle == context_bundle
    assert payload.arguments == arguments


@pytest.mark.asyncio
async def test_stream_chat_uses_manifests_directly(
    chat_service,
    mock_orchestrator,
    test_manifests,
):
    context_bundle: RawContextBundle = {"conversation_trim": []}
    arguments: ToolArgumentsMap = {}

    async def stream_events():
        yield {"type": SSEEventType.FINAL, "text": "Done"}

    mock_orchestrator.stream = stream_events

    async for _ in chat_service.stream_chat(
        conversation_id="conv-123",
        user_question="test question",
        turn_id="comp-123",
        context_bundle=context_bundle,
        arguments=arguments,
        manifests=[test_manifests[0]],
    ):
        pass

    mock_orchestrator.stream.assert_called_once()
    call_args = mock_orchestrator.stream.call_args
    assert call_args[0][0] == [test_manifests[0]]
