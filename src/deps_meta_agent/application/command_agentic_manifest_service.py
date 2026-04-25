import logging

from deps_message_flow.events.publisher import DomainEventPublisher

from deps_meta_agent.constants import AGENTIC_MANIFEST_DESTINATION
from deps_meta_agent.domain.model import (
    AgenticManifest,
    AgenticManifestFactory,
    RawAgenticManifest,
)
from deps_meta_agent.infrastructure.unit_of_work import AbstractUnitOfWork

from .retry_transaction import retry_on_transaction_error

__all__ = ["CommandAgenticManifestService"]


class CommandAgenticManifestService:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        domain_event_publisher: DomainEventPublisher,
    ) -> None:
        self._uow = unit_of_work
        self._domain_event_publisher = domain_event_publisher

        self._logger = logging.getLogger(self.__class__.__name__)

    @retry_on_transaction_error()
    def register(self, raw_manifest: RawAgenticManifest) -> AgenticManifest:
        with self._uow:
            if (manifest := self._uow.agentic_manifest.find_manifest_by_code(raw_manifest["code"])) is None:
                manifest = AgenticManifestFactory.create(
                    code=raw_manifest["code"],
                    name=raw_manifest["name"],
                    description=raw_manifest["description"],
                    endpoint=raw_manifest["endpoint"],
                )

            else:
                manifest.update(
                    name=raw_manifest["name"],
                    description=raw_manifest["description"],
                    endpoint=raw_manifest["endpoint"],
                )

            self._uow.agentic_manifest.save(manifest)

            self._publish_events(manifest)

            self._uow.commit()

        self._logger.info("Agentic manifest with code `%s` and name `%s` registered.", manifest.code, manifest.name)

        return manifest

    @retry_on_transaction_error()
    def delete(self, codes: list[str]) -> None:
        manifests, not_found_codes = [], []
        with self._uow:
            for code in codes:
                if manifest := self._uow.agentic_manifest.find_manifest_by_code(code):
                    manifest.delete()
                    manifests.append(manifest)
                else:
                    not_found_codes.append(code)

            if not_found_codes:
                self._logger.info(
                    "Skipped %d non-existent manifest(s): %s",
                    len(not_found_codes),
                    not_found_codes,
                )

            if manifests:
                self._uow.agentic_manifest.delete_all(manifests)
                for manifest in manifests:
                    self._publish_events(manifest)

            self._uow.commit()

            self._logger.info("Deleted %d agentic manifest(s): %s", len(manifests), [m.code for m in manifests])

    def _publish_events(self, manifest: AgenticManifest) -> None:
        self._domain_event_publisher.publish(
            aggregate_type=AGENTIC_MANIFEST_DESTINATION,
            aggregate_id=manifest.code,
            domain_events=manifest.events,
        )
