import pytest

from deps_meta_agent.domain.model import ICommandAgenticManifestRepository


@pytest.fixture
def unit_of_work(containers):
    return containers.unit_of_work()


@pytest.fixture
def command_agentic_manifest_repository(repositories) -> ICommandAgenticManifestRepository:
    return repositories.command_agentic_manifest()
