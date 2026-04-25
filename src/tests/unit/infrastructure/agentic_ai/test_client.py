import http
from unittest.mock import MagicMock, patch

import pytest
import requests

from deps_meta_agent.domain.exceptions import (
    AgenticAIClientError,
    AgentVendorAlreadyExistsError,
)
from deps_meta_agent.infrastructure.agentic_ai import AgenticAIClient


def test_create_agent_vendor__success__creates_vendor(agentic_ai_client):
    expected_name = "New Vendor"
    expected_description = "New Description"
    expected_base_url = "http://new-vendor:8000"

    mock_response = MagicMock()
    mock_response.status_code = http.HTTPStatus.CREATED
    mock_response.raise_for_status = MagicMock()

    with patch.object(agentic_ai_client._session, "post", return_value=mock_response):
        agentic_ai_client.create_agent_vendor(
            name=expected_name,
            description=expected_description,
            base_url=expected_base_url,
        )

        agentic_ai_client._session.post.assert_called_once()
        call_kwargs = agentic_ai_client._session.post.call_args[1]
        assert call_kwargs["json"]["name"] == expected_name
        assert call_kwargs["json"]["description"] == expected_description
        assert call_kwargs["json"]["baseUrl"] == expected_base_url


def test_create_agent_vendor__with_avatar__includes_avatar_in_payload(agentic_ai_client):
    expected_avatar_url = "http://example.com/avatar.png"

    mock_response = MagicMock()
    mock_response.status_code = http.HTTPStatus.CREATED
    mock_response.raise_for_status = MagicMock()

    with patch.object(agentic_ai_client._session, "post", return_value=mock_response) as mock_post:
        agentic_ai_client.create_agent_vendor(
            name="Vendor",
            description="Description",
            base_url="http://vendor:8000",
            avatar_url=expected_avatar_url,
        )

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["avatarUrl"] == expected_avatar_url


def test_create_agent_vendor__conflict__raises_already_exists_error(agentic_ai_client):
    mock_response = MagicMock()
    mock_response.status_code = http.HTTPStatus.CONFLICT

    with patch.object(agentic_ai_client._session, "post", return_value=mock_response):
        with pytest.raises(AgentVendorAlreadyExistsError) as exc_info:
            agentic_ai_client.create_agent_vendor(
                name="Existing Vendor",
                description="Description",
                base_url="http://vendor:8000",
            )

        assert "already exists" in str(exc_info.value)


def test_create_agent_vendor__http_error__raises_client_error(agentic_ai_client):
    mock_response = MagicMock()
    mock_response.status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    mock_response.raise_for_status.side_effect = requests.HTTPError("Server error")

    with patch.object(agentic_ai_client._session, "post", return_value=mock_response):
        with pytest.raises(AgenticAIClientError) as exc_info:
            agentic_ai_client.create_agent_vendor(
                name="Vendor",
                description="Description",
                base_url="http://vendor:8000",
            )

        assert "Failed to create agent vendor" in str(exc_info.value)


def test_create_agent_vendor__network_error__raises_client_error(agentic_ai_client):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.RequestException("Connection timeout")

    with patch.object(agentic_ai_client._session, "post", return_value=mock_response):
        with pytest.raises(AgenticAIClientError) as exc_info:
            agentic_ai_client.create_agent_vendor(
                name="Vendor",
                description="Description",
                base_url="http://vendor:8000",
            )

        assert "Network error" in str(exc_info.value)
