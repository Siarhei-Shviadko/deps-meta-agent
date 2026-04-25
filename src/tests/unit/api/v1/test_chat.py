import json
from unittest.mock import Mock

import pytest

from deps_meta_agent.constants import V1_API_PREFIX
from deps_meta_agent.domain.exceptions import ManifestNotFound
from deps_meta_agent.infrastructure.adapters.types import SSEEventType

endpoint = V1_API_PREFIX + "/chat"


@pytest.fixture
def mock_chat_service(containers):
    mock_service = Mock()
    containers.chat_service.reset()
    containers.chat_service.override(mock_service)
    yield mock_service
    containers.chat_service.reset_override()
    containers.chat_service.reset()


def build_request_json(
    conversation_id: str = "conv-123",
    turn_id: str = "turn-123",
    user_question: str = "test question",
    active_tool_sets: list[str] | None = None,
    conversation_trim: list[dict] | None = None,
    arguments: dict | None = None,
) -> str:
    return json.dumps(
        {
            "conversationId": conversation_id,
            "turnId": turn_id,
            "userQuestion": user_question,
            "activeToolSets": active_tool_sets or ["tool1"],
            "contextBundle": {"conversationTrim": conversation_trim or []},
            "arguments": arguments or {},
        }
    )


def test_chat_endpoint_successful_streaming(client, mock_chat_service, test_agentic_manifest_1):
    events = [
        {"type": SSEEventType.REASONING, "text": "Thinking..."},
        {"type": SSEEventType.TOOL_CALL, "text": "Calling tool"},
        {"type": SSEEventType.FINAL, "text": "Final answer"},
    ]

    async def stream_events(**kwargs):
        for event in events:
            yield event

    mock_chat_service.validate_chat_preconditions.return_value = [test_agentic_manifest_1]
    mock_chat_service.stream_chat = Mock(side_effect=lambda **kw: stream_events(**kw))

    request_json = build_request_json(active_tool_sets=["tool1"])
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.text
    assert "event: message" in content
    assert "data:" in content

    for event in events:
        event_json = json.dumps({"type": event["type"], "text": event["text"]})
        assert event_json in content

    mock_chat_service.validate_chat_preconditions.assert_called_once_with({"tool1"})
    mock_chat_service.stream_chat.assert_called_once()
    call_kwargs = mock_chat_service.stream_chat.call_args.kwargs
    assert call_kwargs["conversation_id"] == "conv-123"
    assert call_kwargs["user_question"] == "test question"
    assert call_kwargs["turn_id"] == "turn-123"
    assert call_kwargs["manifests"] == [test_agentic_manifest_1]


def test_chat_endpoint_stops_after_final_event(client, mock_chat_service, test_agentic_manifest_1):
    events = [
        {"type": SSEEventType.REASONING, "text": "Thinking..."},
        {"type": SSEEventType.FINAL, "text": "Final answer"},
        {"type": SSEEventType.REASONING, "text": "This should not appear"},
    ]

    async def stream_events(**kwargs):
        for event in events:
            yield event

    mock_chat_service.validate_chat_preconditions.return_value = [test_agentic_manifest_1]
    mock_chat_service.stream_chat = Mock(side_effect=lambda **kw: stream_events(**kw))

    request_json = build_request_json()
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    content = response.text

    final_event_json = json.dumps({"type": SSEEventType.FINAL, "text": "Final answer"})
    assert final_event_json in content

    subsequent_event_json = json.dumps({"type": SSEEventType.REASONING, "text": "This should not appear"})
    assert subsequent_event_json not in content


def test_chat_endpoint_handles_exception(client, mock_chat_service, test_agentic_manifest_1):
    async def stream_events(**kwargs):
        raise ValueError("Test error")
        yield

    mock_chat_service.validate_chat_preconditions.return_value = [test_agentic_manifest_1]
    mock_chat_service.stream_chat = Mock(side_effect=lambda **kw: stream_events(**kw))

    request_json = build_request_json()
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    content = response.text

    assert "event: error" in content
    error_event = json.dumps({"type": "Error", "text": "Test error"})
    assert error_event in content


def test_chat_endpoint_returns_400_when_no_manifests(client, mock_chat_service):
    mock_chat_service.validate_chat_preconditions.side_effect = ManifestNotFound("manifest_code")

    request_json = build_request_json()
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/json"
    response_data = response.json()
    assert response_data["code"] == "manifest_not_found"

    mock_chat_service.validate_chat_preconditions.assert_called_once_with({"tool1"})
    mock_chat_service.stream_chat.assert_not_called()


def test_chat_endpoint_sse_message_formatting(client, mock_chat_service, test_agentic_manifest_1):
    events = [
        {"type": SSEEventType.REASONING, "text": "Test message"},
    ]

    async def stream_events(**kwargs):
        for event in events:
            yield event

    mock_chat_service.validate_chat_preconditions.return_value = [test_agentic_manifest_1]
    mock_chat_service.stream_chat = Mock(side_effect=lambda **kw: stream_events(**kw))

    request_json = build_request_json()
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    content = response.text

    lines = content.split("\n")
    message_lines = [line for line in lines if line.startswith("event: message") or line.startswith("data:")]

    assert len(message_lines) >= 2
    assert "event: message" in message_lines[0] or "data:" in message_lines[0]


def test_chat_endpoint_passes_correct_parameters(client, mock_chat_service, test_agentic_manifest_1):
    conversation_trim = [{"question": "Previous question", "answer": "Previous answer"}]
    arguments = {"tool1": [{"value": "arg1"}]}

    request_json = build_request_json(
        conversation_id="test-conv-id",
        turn_id="test-turn-id",
        user_question="What is the answer?",
        active_tool_sets=["tool1", "tool2"],
        conversation_trim=conversation_trim,
        arguments=arguments,
    )

    events = [{"type": SSEEventType.FINAL, "text": "Done"}]

    async def stream_events(**kwargs):
        for event in events:
            yield event

    mock_chat_service.validate_chat_preconditions.return_value = [test_agentic_manifest_1]
    mock_chat_service.stream_chat = Mock(side_effect=lambda **kw: stream_events(**kw))

    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200

    mock_chat_service.validate_chat_preconditions.assert_called_once_with({"tool1", "tool2"})
    mock_chat_service.stream_chat.assert_called_once()
    call_kwargs = mock_chat_service.stream_chat.call_args.kwargs
    assert call_kwargs["conversation_id"] == "test-conv-id"
    assert call_kwargs["user_question"] == "What is the answer?"
    assert call_kwargs["turn_id"] == "test-turn-id"
    assert call_kwargs["manifests"] == [test_agentic_manifest_1]

    context_bundle = call_kwargs["context_bundle"]
    assert "conversation_trim" in context_bundle
    assert len(context_bundle["conversation_trim"]) == 1
    assert context_bundle["conversation_trim"][0]["question"] == "Previous question"

    call_arguments = call_kwargs["arguments"]
    assert "tool1" in call_arguments
    assert len(call_arguments["tool1"]) == 1
    assert call_arguments["tool1"][0]["value"] == "arg1"
