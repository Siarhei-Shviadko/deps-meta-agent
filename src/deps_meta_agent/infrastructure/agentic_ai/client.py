import logging

import requests

from deps_meta_agent.domain.exceptions import (
    AgenticAIClientError,
    AgentVendorAlreadyExistsError,
)

__all__ = ["AgenticAIClient"]


class AgenticAIClient:
    api_prefix = "/api/agentic-ai/internal"
    agent_vendor_url = "/agent-vendors"

    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self.base_url = base_url
        self._timeout = timeout

        self._logger = logging.getLogger(self.__class__.__name__)

        self._session = requests.Session()
        self._initialize()

    def _initialize(self) -> None:
        self.session.headers.update({"Content-Type": "application/json"})

    @property
    def session(self) -> requests.Session:
        return self._session

    def create_agent_vendor(
        self,
        name: str,
        description: str,
        base_url: str,
        avatar_url: str | None = None,
    ) -> None:
        url = f"{self.base_url}{self.api_prefix}{self.agent_vendor_url}"
        payload = {
            "name": name,
            "description": description,
            "baseUrl": base_url,
            "avatarUrl": avatar_url,
        }

        self._check_response(self.session.post(url, json=payload, timeout=self._timeout))

    def _check_response(self, response: requests.Response) -> None:
        try:
            if response.status_code == 409:  # noqa: WPS432
                raise AgentVendorAlreadyExistsError("Agent vendor already exists")

            response.raise_for_status()
        except requests.HTTPError as e:
            self._logger.error("Failed to create agent vendor: %s", e)
            raise AgenticAIClientError(f"Failed to create agent vendor: {e}") from e
        except requests.RequestException as e:
            self._logger.error("Network error while creating agent vendor: %s", e)
            raise AgenticAIClientError(f"Network error: {e}") from e
