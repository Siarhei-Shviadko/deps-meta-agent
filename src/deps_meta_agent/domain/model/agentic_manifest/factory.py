from datetime import datetime, timezone

from ..shared import Event
from .agent_endpoint import AgentEndpoint
from .events import AgenticManifestCreated
from .model import AgenticManifest
from .types import RawAgentEndpoint

__all__ = ["AgenticManifestFactory"]


class AgenticManifestFactory:
    @classmethod
    def create(cls, code: str, name: str, description: str, endpoint: RawAgentEndpoint) -> AgenticManifest:
        current_timestamp = datetime.now(timezone.utc)
        return AgenticManifest(
            code=code,
            name=name,
            description=description,
            endpoint=AgentEndpoint(
                url=endpoint["url"],
                timeout=endpoint["timeout"],
            ),
            created_at=current_timestamp,
            events=cls._make_events(code=code, created_at=current_timestamp),
        )

    @staticmethod
    def _make_events(code: str, created_at: datetime) -> list[Event]:
        return [AgenticManifestCreated(code=code, created_at=created_at)]
