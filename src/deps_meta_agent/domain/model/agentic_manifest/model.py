from datetime import datetime, timezone

from ..shared import Entity, Event, Guard, ImmutableCheck
from .agent_endpoint import AgentEndpoint
from .events import AgenticManifestDeleted
from .types.raw_agent_endpoint import RawAgentEndpoint

__all__ = ["AgenticManifest"]


class AgenticManifest(metaclass=Entity):
    code = Guard[str](str, ImmutableCheck())
    name = Guard[str](str)
    description = Guard[str](str)
    endpoint = Guard[AgentEndpoint](AgentEndpoint)
    created_at = Guard[datetime](datetime, ImmutableCheck())
    updated_at = Guard[datetime](datetime)

    def __init__(
        self,
        code: str,
        name: str,
        description: str,
        endpoint: AgentEndpoint,
        created_at: datetime,
        updated_at: datetime | None = None,
        *,
        events: list[Event] | None = None,
    ) -> None:
        self.code = code
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.created_at = created_at
        self.updated_at = updated_at or created_at

        self.events = events or []

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.code == self.code

    def update(self, name: str, description: str, endpoint: RawAgentEndpoint) -> None:
        self.name = name
        self.description = description
        self.endpoint = AgentEndpoint.from_raw(endpoint)
        self.updated_at = datetime.now(timezone.utc)

    def delete(self) -> None:
        self.events.append(AgenticManifestDeleted(self.code))
