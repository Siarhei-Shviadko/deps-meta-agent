import json
from unittest.mock import Mock

import pytest
from langchain_core.language_models import BaseChatModel

from deps_meta_agent.constants import V1_API_PREFIX
from deps_meta_agent.infrastructure.adapters.agent_http_client import (
    HttpAgentStreamClient,
)
from deps_meta_agent.infrastructure.adapters.types import SSEEvent, SSEEventType
from deps_meta_agent.infrastructure.agent.agent_workflow_factory.schemas import (
    AgentSelectionOutput,
    ResponseEvaluationOutput,
)

endpoint = V1_API_PREFIX + "/chat"


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


def parse_sse_response(content: str) -> list[dict]:
    events = []
    lines = content.split("\n")
    current_data = []

    for line in lines:
        line = line.rstrip("\r")
        if line.startswith("data:"):
            data_value = line[5:].lstrip()
            current_data.append(data_value)
        elif not line and current_data:
            data_value = "\n".join(current_data)
            if data_value:
                try:
                    event_data = json.loads(data_value)
                    events.append(event_data)
                except json.JSONDecodeError:
                    pass
            current_data = []

    if current_data:
        data_value = "\n".join(current_data)
        if data_value:
            try:
                event_data = json.loads(data_value)
                events.append(event_data)
            except json.JSONDecodeError:
                pass

    return events


def setup_agent_http_client_mock(
    mock_client: Mock,
    events: list[SSEEvent],
) -> None:
    async def stream_chat_mock(*args, **kwargs):
        for event in events:
            yield event

    mock_client.stream_chat = Mock(side_effect=stream_chat_mock)


@pytest.fixture
def mock_llm():
    mock = Mock(spec=BaseChatModel)
    return mock


@pytest.fixture
def mock_model_provider_factory(containers, mock_llm):
    mock_factory = Mock()
    mock_factory.create_llm.return_value = mock_llm

    containers.model_provider_factory.reset()
    containers.model_provider_factory.override(mock_factory)
    yield mock_factory
    containers.model_provider_factory.reset_override()
    containers.model_provider_factory.reset()


@pytest.fixture
def mock_agent_http_client(containers):
    mock_client = Mock(spec=HttpAgentStreamClient)

    containers.agent_http_client.reset()
    containers.agent_http_client.override(mock_client)
    yield mock_client
    containers.agent_http_client.reset_override()
    containers.agent_http_client.reset()


@pytest.fixture
def setup_orchestrator_mocks(
    containers,
    mock_model_provider_factory,
    mock_agent_http_client,
):
    containers.orchestrator_workflow_factory.reset()
    containers.meta_agent_orchestrator.reset()
    containers.chat_service.reset()

    yield

    containers.orchestrator_workflow_factory.reset()
    containers.meta_agent_orchestrator.reset()
    containers.chat_service.reset()


def test_chat__successful_streaming__returns_sse_events(
    client,
    unit_of_work,
    add_agentic_manifests,
    test_agentic_manifests,
    mock_llm,
    mock_model_provider_factory,
    mock_agent_http_client,
    setup_orchestrator_mocks,
):
    manifest = test_agentic_manifests[0]

    agent_events = [
        {"type": SSEEventType.REASONING, "text": "Agent thinking..."},
        {"type": SSEEventType.TOOL_CALL, "text": "Calling tool"},
        {"type": SSEEventType.FINAL, "text": "Final answer from agent"},
    ]

    selection_mock = Mock()
    selection_mock.invoke.return_value = AgentSelectionOutput(
        selected_agent_code=manifest.code,
        reasoning="Test reasoning",
    )

    evaluation_mock = Mock()
    evaluation_mock.invoke.return_value = ResponseEvaluationOutput(
        satisfied=True,
        reasoning="Test evaluation",
    )

    def with_structured_output_side_effect(output_type):
        if output_type == AgentSelectionOutput:
            return selection_mock
        return evaluation_mock

    mock_llm.with_structured_output.side_effect = with_structured_output_side_effect

    setup_agent_http_client_mock(mock_agent_http_client, agent_events)

    request_json = build_request_json(active_tool_sets=[manifest.code])
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    print(response.text)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    events = parse_sse_response(response.text)
    assert len(events) >= 1

    final_events = [e for e in events if e.get("type") == SSEEventType.FINAL.value]
    assert len(final_events) > 0
    assert "Final answer from agent" in final_events[0]["text"]


def test_chat__no_manifests_found__returns_error(
    client,
    unit_of_work,
    mock_llm,
    mock_model_provider_factory,
    mock_agent_http_client,
    setup_orchestrator_mocks,
):
    request_json = build_request_json(active_tool_sets=["non-existent-tool"])
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 400


def test_chat__agent_selection_and_evaluation_flow(
    client,
    unit_of_work,
    add_agentic_manifests,
    test_agentic_manifests,
    mock_llm,
    mock_model_provider_factory,
    mock_agent_http_client,
    setup_orchestrator_mocks,
):
    manifest = test_agentic_manifests[0]

    agent_events = [
        {"type": SSEEventType.REASONING, "text": "Processing..."},
        {"type": SSEEventType.FINAL, "text": "Agent response"},
    ]

    selection_mock = Mock()
    selection_mock.invoke.return_value = AgentSelectionOutput(
        selected_agent_code=manifest.code,
        reasoning="Selected for test",
    )

    evaluation_mock = Mock()
    evaluation_mock.invoke.return_value = ResponseEvaluationOutput(
        satisfied=True,
        reasoning="Response is satisfactory",
    )

    def with_structured_output_side_effect(output_type):
        if output_type == AgentSelectionOutput:
            return selection_mock
        return evaluation_mock

    mock_llm.with_structured_output.side_effect = with_structured_output_side_effect

    setup_agent_http_client_mock(mock_agent_http_client, agent_events)

    request_json = build_request_json(active_tool_sets=[manifest.code])
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    events = parse_sse_response(response.text)

    final_events = [e for e in events if e.get("type") == SSEEventType.FINAL.value]
    assert len(final_events) > 0

    # Verify LLM was used for agent selection
    mock_llm.with_structured_output.assert_called()


def test_chat__multiple_agents_attempted_when_first_fails(
    client,
    unit_of_work,
    add_agentic_manifests,
    test_agentic_manifests,
    mock_llm,
    mock_model_provider_factory,
    mock_agent_http_client,
    setup_orchestrator_mocks,
):
    manifest1 = test_agentic_manifests[0]
    manifest2 = test_agentic_manifests[1]

    first_agent_events = [
        {"type": SSEEventType.FINAL, "text": "First agent response"},
    ]

    second_agent_events = [
        {"type": SSEEventType.FINAL, "text": "Second agent response"},
    ]

    selection_call_count = {"count": 0}
    evaluation_call_count = {"count": 0}
    adapter_call_count = {"count": 0}

    selection_mock1 = Mock()
    selection_mock1.invoke.return_value = AgentSelectionOutput(
        selected_agent_code=manifest1.code,
        reasoning="First attempt",
    )

    selection_mock2 = Mock()
    selection_mock2.invoke.return_value = AgentSelectionOutput(
        selected_agent_code=manifest2.code,
        reasoning="Second attempt",
    )

    evaluation_mock1 = Mock()
    evaluation_mock1.invoke.return_value = ResponseEvaluationOutput(
        satisfied=False,
        reasoning="Not satisfied",
    )

    evaluation_mock2 = Mock()
    evaluation_mock2.invoke.return_value = ResponseEvaluationOutput(
        satisfied=True,
        reasoning="Satisfied",
    )

    def with_structured_output_side_effect(output_type):
        if output_type == AgentSelectionOutput:
            selection_call_count["count"] += 1
            if selection_call_count["count"] == 1:
                return selection_mock1
            return selection_mock2
        else:
            evaluation_call_count["count"] += 1
            if evaluation_call_count["count"] == 1:
                return evaluation_mock1
            return evaluation_mock2

    mock_llm.with_structured_output.side_effect = with_structured_output_side_effect

    async def adapter_stream_side_effect(*args, **kwargs):
        adapter_call_count["count"] += 1
        if adapter_call_count["count"] == 1:
            for event in first_agent_events:
                yield event
        else:
            for event in second_agent_events:
                yield event

    mock_agent_http_client.stream_chat = adapter_stream_side_effect

    request_json = build_request_json(active_tool_sets=[manifest1.code, manifest2.code])
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
    events = parse_sse_response(response.text)

    final_events = [e for e in events if e.get("type") == SSEEventType.FINAL.value]
    assert len(final_events) > 0


def test_chat__context_parsing_and_propagation(
    client,
    unit_of_work,
    add_agentic_manifests,
    test_agentic_manifests,
    mock_llm,
    mock_model_provider_factory,
    mock_agent_http_client,
    setup_orchestrator_mocks,
):
    manifest = test_agentic_manifests[0]

    conversation_trim = [{"question": "Previous question?", "answer": "Previous answer."}]
    arguments = {"tool1": [{"value": "test_value"}]}

    agent_events = [
        {"type": SSEEventType.FINAL, "text": "Response"},
    ]

    selection_mock = Mock()
    selection_mock.invoke.return_value = AgentSelectionOutput(
        selected_agent_code=manifest.code,
        reasoning="Test reasoning",
    )

    evaluation_mock = Mock()
    evaluation_mock.invoke.return_value = ResponseEvaluationOutput(
        satisfied=True,
        reasoning="Test evaluation",
    )

    def with_structured_output_side_effect(output_type):
        if output_type == AgentSelectionOutput:
            return selection_mock
        return evaluation_mock

    mock_llm.with_structured_output.side_effect = with_structured_output_side_effect

    setup_agent_http_client_mock(mock_agent_http_client, agent_events)

    request_json = build_request_json(
        active_tool_sets=[manifest.code],
        conversation_trim=conversation_trim,
        arguments=arguments,
    )
    query_params = {"request": request_json}

    response = client.get(endpoint, params=query_params)

    assert response.status_code == 200
