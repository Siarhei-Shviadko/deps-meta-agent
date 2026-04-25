import pytest

from deps_meta_agent import constants


class TestDebug:
    endpoint = constants.BASE_API_PREFIX

    def test_debug_endpoint_return_500(self, client):
        with pytest.raises(ValueError):
            client.get(f"{self.endpoint}/debug/500")
