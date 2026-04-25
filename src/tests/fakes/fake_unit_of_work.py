from deps_meta_agent.infrastructure.unit_of_work import AbstractUnitOfWork

__all__ = ["FakeUnitOfWork"]


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        agentic_manifests,
    ) -> None:
        self.agentic_manifests = agentic_manifests

    def __enter__(self) -> None:
        pass

    def commit(self):
        pass

    def rollback(self):
        pass
