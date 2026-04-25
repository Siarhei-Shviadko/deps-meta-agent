import logging

from deps_meta_agent.domain.exceptions import AgentVendorAlreadyExistsError
from deps_meta_agent.infrastructure.agentic_ai import AgenticAIClient

__all__ = ["AgentVendorRegistrationService"]


class AgentVendorRegistrationService:
    def __init__(
        self,
        agentic_ai_client: AgenticAIClient,
        agent_vendor_name: str,
        agent_vendor_description: str,
        meta_agent_base_url: str,
    ) -> None:
        self._client = agentic_ai_client

        self._name = agent_vendor_name
        self._description = agent_vendor_description
        self._base_url = meta_agent_base_url

        self._logger = logging.getLogger(self.__class__.__name__)

    def register(self) -> None:
        try:
            self._client.create_agent_vendor(
                name=self._name,
                description=self._description,
                base_url=self._base_url,
            )
            self._logger.info("Successfully registered agent vendor '%s'", self._name)

        except AgentVendorAlreadyExistsError:
            self._logger.info("Agent vendor '%s' already exists", self._name)
