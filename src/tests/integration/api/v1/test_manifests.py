import http
from random import choice, randint
from uuid import uuid4

from deps_meta_agent.constants import V1_API_PREFIX


def test_register_manifest__new__ok(client):
    payload = {
        "code": uuid4().hex,
        "name": uuid4().hex,
        "description": uuid4().hex,
        "url": uuid4().hex,
        "timeout": randint(1, 10),
    }
    response = client.post(f"{V1_API_PREFIX}/manifests", json=payload)

    assert response.status_code == http.HTTPStatus.CREATED
    assert response.json()["code"]


def test_register_manifest__exists__ok(client, unit_of_work, add_agentic_manifests, test_agentic_manifests):
    existing_manifest = choice(test_agentic_manifests)

    payload = {
        "code": existing_manifest.code,
        "name": uuid4().hex,
        "description": existing_manifest.description,
        "url": existing_manifest.endpoint.url,
        "timeout": existing_manifest.endpoint.timeout,
    }

    response = client.post(f"{V1_API_PREFIX}/manifests", json=payload)

    assert response.status_code == http.HTTPStatus.CREATED
    assert response.json()["code"]

    with unit_of_work:
        saved_manifest = unit_of_work.agentic_manifest.find_manifest_by_code(existing_manifest.code)

    assert saved_manifest.description == payload["description"]


def test_delete_manifests__existing__no_content(client, add_agentic_manifests, test_agentic_manifests):
    codes = [m.code for m in test_agentic_manifests]
    query_params = "&".join([f"code={code}" for code in codes])

    response = client.delete(f"{V1_API_PREFIX}/manifests?{query_params}")

    assert response.status_code == http.HTTPStatus.NO_CONTENT


def test_delete_manifests__single__no_content(client, add_agentic_manifests, test_agentic_manifest_1):
    response = client.delete(f"{V1_API_PREFIX}/manifests?code={test_agentic_manifest_1.code}")

    assert response.status_code == http.HTTPStatus.NO_CONTENT


def test_delete_manifests__not_found__no_content(client):
    non_existent_code = uuid4().hex

    response = client.delete(f"{V1_API_PREFIX}/manifests?code={non_existent_code}")

    assert response.status_code == http.HTTPStatus.NO_CONTENT


def test_delete_manifests__partial_not_found__no_content(client, add_agentic_manifests, test_agentic_manifest_1):
    non_existent_code = uuid4().hex
    query_params = f"code={test_agentic_manifest_1.code}&code={non_existent_code}"

    response = client.delete(f"{V1_API_PREFIX}/manifests?{query_params}")

    assert response.status_code == http.HTTPStatus.NO_CONTENT
