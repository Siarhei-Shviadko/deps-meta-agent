from random import choice, randint
from uuid import uuid4

import pytest

from deps_meta_agent.domain.model import RawAgentEndpoint


def test_save_manifest__saved(unit_of_work, test_agentic_manifest_1):
    with unit_of_work:
        unit_of_work.agentic_manifest.save(test_agentic_manifest_1)

        saved_agentic_manifest = unit_of_work.agentic_manifest.find_manifest_by_code(test_agentic_manifest_1.code)

    assert saved_agentic_manifest.code == test_agentic_manifest_1.code
    assert saved_agentic_manifest.name == test_agentic_manifest_1.name
    assert saved_agentic_manifest.description == test_agentic_manifest_1.description
    assert saved_agentic_manifest.created_at == test_agentic_manifest_1.created_at
    assert saved_agentic_manifest.updated_at == test_agentic_manifest_1.updated_at
    assert saved_agentic_manifest.endpoint == test_agentic_manifest_1.endpoint


def test_find_manifest__by_code__manifest_exists__found(unit_of_work, add_agentic_manifests, test_agentic_manifests):
    expected_manifest = choice(test_agentic_manifests)
    with unit_of_work:
        saved_manifest = unit_of_work.agentic_manifest.find_manifest_by_code(expected_manifest.code)

    assert saved_manifest.code == expected_manifest.code
    assert saved_manifest.name == expected_manifest.name
    assert saved_manifest.description == expected_manifest.description
    assert saved_manifest.created_at == expected_manifest.created_at
    assert saved_manifest.updated_at == expected_manifest.updated_at
    assert saved_manifest.endpoint == expected_manifest.endpoint


def test_find_manifest__by_code__manifest_doesnt_exist__no_error(
    unit_of_work, add_agentic_manifests, test_agentic_manifests
):
    with unit_of_work:
        saved_manifest = unit_of_work.agentic_manifest.find_manifest_by_code("fake_code")

    assert saved_manifest is None


def test_delete_all_manifests__deleted(unit_of_work, add_agentic_manifests, test_agentic_manifests):
    with unit_of_work:
        unit_of_work.agentic_manifest.delete_all(test_agentic_manifests)

        for manifest in test_agentic_manifests:
            assert unit_of_work.agentic_manifest.find_manifest_by_code(manifest.code) is None


def test_save_manifest__manifest_exists__updated(unit_of_work, add_agentic_manifests, test_agentic_manifests):
    source_manifest = choice(test_agentic_manifests)

    expected_name = uuid4().hex
    expected_description = uuid4().hex
    expected_endpoint = RawAgentEndpoint(url=uuid4().hex, timeout=randint(1, 100))

    source_manifest.update(name=expected_name, description=expected_description, endpoint=expected_endpoint)

    with unit_of_work:
        unit_of_work.agentic_manifest.save(source_manifest)

        saved_manifest = unit_of_work.agentic_manifest.find_manifest_by_code(source_manifest.code)

        assert saved_manifest.name == expected_name
        assert saved_manifest.description == expected_description
        assert saved_manifest.endpoint.url == expected_endpoint["url"]
        assert saved_manifest.endpoint.timeout == expected_endpoint["timeout"]
