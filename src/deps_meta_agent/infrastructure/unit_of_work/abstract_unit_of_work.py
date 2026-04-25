import abc

from deps_meta_agent.domain.model import ICommandAgenticManifestRepository

__all__ = ["AbstractUnitOfWork"]


class AbstractUnitOfWork(abc.ABC):
    agentic_manifests: ICommandAgenticManifestRepository

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError
