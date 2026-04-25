import pytest

from deps_meta_agent.infrastructure.agentic_ai import AgenticAIClient


@pytest.fixture
def agentic_ai_client() -> AgenticAIClient:
    return AgenticAIClient(
        base_url="http://test-agentic-ai:8000",
        timeout=30,
    )
