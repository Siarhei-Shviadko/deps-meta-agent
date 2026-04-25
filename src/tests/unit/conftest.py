import pytest

from tests.fakes import FakeCommandAgenticManifestRepository, FakeUnitOfWork


@pytest.fixture
def postgres_session_mock(mocker, containers):
    mock = mocker.Mock(containers.datasources.postgres_session())
    containers.datasources.postgres_session.override(mock)

    yield mock

    containers.datasources.postgres_session.reset_override()


@pytest.fixture(autouse=True, scope="function")
def fake_unit_of_work(
    containers,
):
    fuow = FakeUnitOfWork(agentic_manifests=FakeCommandAgenticManifestRepository())

    containers.unit_of_work.override(fuow)

    yield fuow

    containers.unit_of_work.reset_override()
