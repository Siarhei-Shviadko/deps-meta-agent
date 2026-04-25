from typing import Self

from deps_meta_agent.domain.model import AgenticManifest

from ..base import ConfiguredBaseModel

__all__ = ["RegisterManifestRequest", "RegisterManifestResponse"]


class RegisterManifestRequest(ConfiguredBaseModel):
    code: str
    name: str
    description: str
    url: str
    timeout: int


class RegisterManifestResponse(ConfiguredBaseModel):
    code: str

    @classmethod
    def from_domain(cls, manifest: AgenticManifest) -> Self:
        return cls(
            code=manifest.code,
        )
