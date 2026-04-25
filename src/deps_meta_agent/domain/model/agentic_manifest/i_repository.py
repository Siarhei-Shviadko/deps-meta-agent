from abc import ABC, abstractmethod

from .model import AgenticManifest

__all__ = ["ICommandAgenticManifestRepository"]


class ICommandAgenticManifestRepository(ABC):
    @abstractmethod
    def find_manifest_by_code(self, code: str) -> AgenticManifest | None:
        ...  # noqa: WPS428

    @abstractmethod
    def find_manifests_by_codes(self, codes: list[str]) -> list[AgenticManifest]:
        ...  # noqa: WPS428

    @abstractmethod
    def save(self, manifest: AgenticManifest) -> None:
        ...  # noqa: WPS428

    @abstractmethod
    def delete_all(self, manifests: list[AgenticManifest]) -> None:
        ...  # noqa: WPS428
