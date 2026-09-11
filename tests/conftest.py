from unittest.mock import Mock

import pytest
import requests


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("Tests must mock HTTP requests; live network access is disabled")
    monkeypatch.setattr(requests.sessions.Session, "request", fail)


@pytest.fixture
def response():
    def make(payload, status=200):
        result = Mock(status_code=status)
        result.json.return_value = payload
        return result
    return make
