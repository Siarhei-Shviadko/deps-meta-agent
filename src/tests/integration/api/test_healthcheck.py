from http import HTTPStatus

from deps_meta_agent import constants

endpoint = constants.BASE_API_PREFIX


def test_healthcheck__connection_work__200(client):
    response = client.get(f"{endpoint}/healthcheck")

    assert response.status_code == HTTPStatus.OK
