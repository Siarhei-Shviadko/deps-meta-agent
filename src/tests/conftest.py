import asyncio
import random
from typing import Generator
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from deps_meta_agent import api
from deps_meta_agent.domain.model import (
    AgenticManifest,
    AgenticManifestFactory,
    RawAgentEndpoint,
    RawAgenticManifest,
)
from deps_meta_agent.entrypoint import create_fastapi
from deps_meta_agent.infrastructure.access_management import user


@pytest.fixture(scope="session")
def app() -> FastAPI:
    fastapi_app = create_fastapi()
    yield fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def tenant_id():
    return uuid4().hex


@pytest.fixture
def this_user(tenant_id):
    return dict(
        subject="Test",
        groups=[tenant_id],
        token="token",
        roles=[],
        organisation=tenant_id,
    )


@pytest.fixture(autouse=True)
def set_this_user(this_user):
    user.set(this_user)


@pytest.fixture(autouse=True)
def reset_sse_app_status():
    """Reset SSE app status to avoid event loop issues between tests."""
    from sse_starlette.sse import AppStatus

    # Reset the event to avoid "bound to a different event loop" errors
    AppStatus.should_exit_event = asyncio.Event()
    yield
    # Reset again after test
    AppStatus.should_exit_event = asyncio.Event()


@pytest.fixture(autouse=True)
def mocked_middleware(monkeypatch, mocker):
    monkeypatch.setattr(api.auth, "set_user_from_token", mocker.Mock({}))


@pytest.fixture(scope="session")
def containers(app):
    return app.containers


@pytest.fixture(autouse=True, scope="session")
def domain_event_publisher_session_mock(containers):
    mock = Mock(containers.domain_event_publisher())
    containers.domain_event_publisher.override(mock)

    yield mock

    containers.domain_event_publisher.reset_override()


@pytest.fixture(autouse=True)
def domain_event_publisher_mock(domain_event_publisher_session_mock):
    domain_event_publisher_session_mock.reset_mock()

    yield domain_event_publisher_session_mock


@pytest.fixture
def repositories(containers):
    return containers.repositories


@pytest.fixture
def command_agentic_manifest_service(containers):
    return containers.command_agentic_manifest_service()


@pytest.fixture
def test_agentic_manifest_1() -> AgenticManifest:
    agentic_manifest = AgenticManifestFactory.create(
        code=uuid4().hex,
        name=uuid4().hex,
        description=uuid4().hex,
        endpoint=RawAgentEndpoint(url=uuid4().hex, timeout=random.randint(1, 100)),
    )

    agentic_manifest.events.clear()

    return agentic_manifest


@pytest.fixture
def test_agentic_manifest_2() -> AgenticManifest:
    agentic_manifest = AgenticManifestFactory.create(
        code=uuid4().hex,
        name=uuid4().hex,
        description=uuid4().hex,
        endpoint=RawAgentEndpoint(url=uuid4().hex, timeout=random.randint(1, 100)),
    )

    agentic_manifest.events.clear()

    return agentic_manifest


@pytest.fixture
def test_agentic_manifests(test_agentic_manifest_1, test_agentic_manifest_2) -> list[AgenticManifest]:
    return [test_agentic_manifest_1, test_agentic_manifest_2]


@pytest.fixture
def add_agentic_manifests(unit_of_work, test_agentic_manifests) -> Generator:
    with unit_of_work:
        for manifest in test_agentic_manifests:
            unit_of_work.agentic_manifest.save(manifest)

        unit_of_work.commit()

        yield


@pytest.fixture
def test_raw_agentic_manifest() -> RawAgenticManifest:
    return RawAgenticManifest(
        code=uuid4().hex,
        name=uuid4().hex,
        description=uuid4().hex,
        endpoint=RawAgentEndpoint(url=uuid4().hex, timeout=random.randint(1, 100)),
    )
