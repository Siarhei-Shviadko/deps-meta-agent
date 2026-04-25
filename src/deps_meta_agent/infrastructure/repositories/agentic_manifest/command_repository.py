from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session

from deps_meta_agent.domain.model import ICommandAgenticManifestRepository
from deps_meta_agent.domain.model.agentic_manifest.model import AgenticManifest

from ..tables import agentic_manifest_table
from .mappers import AgenticManifestMapper

__all__ = ["CommandAgenticManifestRepository"]


class CommandAgenticManifestRepository(ICommandAgenticManifestRepository):
    def __init__(self, connection: Session) -> None:
        self._connection = connection

    def save(self, manifest: AgenticManifest) -> None:
        insert_query = insert(agentic_manifest_table)
        save_query = insert_query.on_conflict_do_update(
            constraint=agentic_manifest_table.primary_key,
            set_=dict(insert_query.excluded),
        ).values(**AgenticManifestMapper.to_dict(manifest))

        self._connection.execute(save_query)

    def find_manifest_by_code(self, code: str) -> AgenticManifest | None:
        query = select(agentic_manifest_table).where(agentic_manifest_table.c.code == code)

        result = self._connection.execute(query)

        return AgenticManifestMapper.from_mapping(result.mappings().first()) if self._has_rows(result) else None

    def find_manifests_by_codes(self, codes: list[str]) -> list[AgenticManifest]:
        if not codes:
            return []

        query = select(agentic_manifest_table).where(agentic_manifest_table.c.code.in_(codes))

        result = self._connection.execute(query)

        return [AgenticManifestMapper.from_mapping(row) for row in result.mappings().all()]

    def delete_all(self, manifests: list[AgenticManifest]) -> None:
        query = delete(agentic_manifest_table).where(
            agentic_manifest_table.c.code.in_({manifest.code for manifest in manifests}),
        )

        self._connection.execute(query)

    @staticmethod
    def _has_rows(result: CursorResult) -> bool:
        return result.rowcount > 0
