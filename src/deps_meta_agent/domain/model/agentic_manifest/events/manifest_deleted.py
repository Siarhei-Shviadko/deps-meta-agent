from dataclasses import dataclass

from ...shared import Event

__all__ = ["AgenticManifestDeleted"]


@dataclass
class AgenticManifestDeleted(Event):
    code: str
