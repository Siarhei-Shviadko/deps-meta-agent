import logging
from typing import Optional

from deps_meta_agent.domain.model import (
    AgenticManifest,
    ICommandAgenticManifestRepository,
)

__all__ = ["FakeCommandAgenticManifestRepository"]


class FakeCommandAgenticManifestRepository(ICommandAgenticManifestRepository):
    def __init__(self, manifests: Optional[list[AgenticManifest]] = None) -> None:
        self._db: dict[str, AgenticManifest] = {manifest.code: manifest for manifest in manifests} if manifests else {}

        self._logger = logging.getLogger(self.__class__.__name__)

    def find_manifest_by_code(self, code: str) -> Optional[AgenticManifest]:
        return self._db.get(code)

    def find_manifests_by_codes(self, codes: list[str]) -> list[AgenticManifest]:
        return [self._db[code] for code in codes if code in self._db]

    def save(self, manifest: AgenticManifest) -> None:
        self._db[manifest.code] = manifest

    def delete_all(self, manifests: list[AgenticManifest]) -> None:
        for manifest in manifests:
            self._db.pop(manifest.code, None)
