from dataclasses import dataclass
from datetime import datetime

from ...shared import Event

__all__ = ["AgenticManifestCreated"]


@dataclass
class AgenticManifestCreated(Event):
    code: str
    created_at: datetime | str

    def __post_init__(self):
        if isinstance(self.created_at, datetime):
            self.created_at = self.created_at.isoformat()
