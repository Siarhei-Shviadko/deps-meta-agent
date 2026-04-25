from uuid import uuid4


def test_register_manifest__new__created(command_agentic_manifest_service, test_raw_agentic_manifest):
    manifest = command_agentic_manifest_service.register(test_raw_agentic_manifest)

    assert manifest.code == test_raw_agentic_manifest["code"]
    assert manifest.name == test_raw_agentic_manifest["name"]
    assert manifest.description == test_raw_agentic_manifest["description"]
    assert manifest.endpoint.url == test_raw_agentic_manifest["endpoint"]["url"]
    assert manifest.endpoint.timeout == test_raw_agentic_manifest["endpoint"]["timeout"]


def test_register_manifest__exists__updated(command_agentic_manifest_service, test_raw_agentic_manifest):
    command_agentic_manifest_service.register(test_raw_agentic_manifest)
    test_raw_agentic_manifest["name"] = uuid4().hex

    manifest = command_agentic_manifest_service.register(test_raw_agentic_manifest)

    assert manifest.code == test_raw_agentic_manifest["code"]
    assert manifest.name == test_raw_agentic_manifest["name"]
    assert manifest.description == test_raw_agentic_manifest["description"]
    assert manifest.endpoint.url == test_raw_agentic_manifest["endpoint"]["url"]
    assert manifest.endpoint.timeout == test_raw_agentic_manifest["endpoint"]["timeout"]


def test_delete_manifests__existing__deleted(
    command_agentic_manifest_service, unit_of_work, add_agentic_manifests, test_agentic_manifests
):
    codes = [m.code for m in test_agentic_manifests]

    command_agentic_manifest_service.delete(codes)

    with unit_of_work:
        for code in codes:
            manifest = unit_of_work.agentic_manifest.find_manifest_by_code(code)
            assert manifest is None


def test_delete_manifests__single__deleted(
    command_agentic_manifest_service, unit_of_work, add_agentic_manifests, test_agentic_manifest_1
):
    codes = [test_agentic_manifest_1.code]

    command_agentic_manifest_service.delete(codes)

    with unit_of_work:
        manifest = unit_of_work.agentic_manifest.find_manifest_by_code(test_agentic_manifest_1.code)
        assert manifest is None


def test_delete_manifests__partial_not_found__deletes_existing(
    command_agentic_manifest_service, unit_of_work, add_agentic_manifests, test_agentic_manifest_1
):
    non_existent_code = uuid4().hex
    codes = [test_agentic_manifest_1.code, non_existent_code]

    command_agentic_manifest_service.delete(codes)

    with unit_of_work:
        manifest = unit_of_work.agentic_manifest.find_manifest_by_code(test_agentic_manifest_1.code)
        assert manifest is None
