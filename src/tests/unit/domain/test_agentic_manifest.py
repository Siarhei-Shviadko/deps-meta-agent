import random
from uuid import uuid4

import pytest

from deps_meta_agent.domain.model import (
    AgenticManifestCreated,
    AgenticManifestDeleted,
    AgenticManifestFactory,
    RawAgentEndpoint,
)


def test_agentic_manifest_factory():
    expected_code = uuid4().hex
    expected_name = uuid4().hex
    expected_desc = uuid4().hex
    expected_endpoint = RawAgentEndpoint(url=uuid4().hex, timeout=random.randint(1, 100))

    manifest = AgenticManifestFactory.create(
        code=expected_code,
        name=expected_name,
        description=expected_desc,
        endpoint=expected_endpoint,
    )

    assert manifest.code == expected_code
    assert manifest.name == expected_name
    assert manifest.description == expected_desc
    assert manifest.endpoint.url == expected_endpoint["url"]
    assert manifest.endpoint.timeout == expected_endpoint["timeout"]

    assert len(manifest.events) == 1

    target_event = manifest.events[0]

    assert isinstance(target_event, AgenticManifestCreated)
    assert target_event.code == expected_code
    assert target_event.created_at == manifest.created_at.isoformat()


def test_agentic_manifest_update(test_agentic_manifests):
    target_manifest = random.choice(test_agentic_manifests)

    expected_name = uuid4().hex
    expected_desc = uuid4().hex
    expected_endpoint = RawAgentEndpoint(url=uuid4().hex, timeout=random.randint(1, 100))
    original_updated_at = target_manifest.updated_at
    original_created_at = target_manifest.created_at

    target_manifest.update(name=expected_name, description=expected_desc, endpoint=expected_endpoint)

    assert target_manifest.name == expected_name
    assert target_manifest.description == expected_desc
    assert target_manifest.endpoint.url == expected_endpoint["url"]
    assert target_manifest.endpoint.timeout == expected_endpoint["timeout"]
    assert target_manifest.updated_at != original_updated_at
    assert target_manifest.created_at == original_created_at


def test_delete_agentic_manifest__event_added(test_agentic_manifests):
    target_manifest = random.choice(test_agentic_manifests)

    target_manifest.delete()

    assert len(target_manifest.events) == 1
    assert isinstance(target_manifest.events[0], AgenticManifestDeleted)
    assert target_manifest.events[0].code == target_manifest.code
