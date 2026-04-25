from typing import Any, Mapping

from deps_meta_agent.domain.model import AgentEndpoint

__all__ = ["AgentEndpointMapper"]


class AgentEndpointMapper:
    @classmethod
    def to_dict(cls, endpoint: AgentEndpoint) -> dict[str, Any]:
        return {
            "url": endpoint.url,
            "timeout": endpoint.timeout,
        }

    @classmethod
    def from_mapping(cls, endpoint: Mapping[str, Any]) -> AgentEndpoint:
        return AgentEndpoint(
            url=endpoint["url"],
            timeout=endpoint["timeout"],
        )
