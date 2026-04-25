from typing import Any, Mapping

from deps_meta_agent.domain.model import AgenticManifest

from .agent_endpoint import AgentEndpointMapper

__all__ = ["AgenticManifestMapper"]


class AgenticManifestMapper:
    @classmethod
    def to_dict(cls, agentic_manifest: AgenticManifest) -> dict[str, Any]:
        return {
            "code": agentic_manifest.code,
            "name": agentic_manifest.name,
            "description": agentic_manifest.description,
            "endpoint": AgentEndpointMapper.to_dict(agentic_manifest.endpoint),
            "created_at": agentic_manifest.created_at,
            "updated_at": agentic_manifest.updated_at,
        }

    @classmethod
    def from_mapping(cls, agentic_manifest: Mapping[str, Any]) -> AgenticManifest:
        return AgenticManifest(
            code=agentic_manifest["code"],
            name=agentic_manifest["name"],
            description=agentic_manifest["description"],
            endpoint=AgentEndpointMapper.from_mapping(agentic_manifest["endpoint"]),
            created_at=agentic_manifest["created_at"],
            updated_at=agentic_manifest["updated_at"],
        )
