from unittest.mock import patch

import pytest

from src.hunterio_client import HunterIOClient
from src.utils import APIError


@patch("src.utils.requests.get")
def test_full_name_request(get, response):
    get.return_value = response({"data": {"email": "john@example.com"}})
    assert HunterIOClient("secret").generate_email("John & Jane Doe", "example.com") == "john@example.com"
    get.assert_called_once_with(
        "https://api.hunter.io/v2/email-finder",
        params={"full_name": "John & Jane Doe", "domain": "example.com", "api_key": "secret"},
        timeout=(5, 180), allow_redirects=False,
    )


@patch("src.utils.requests.get")
def test_separate_names(get, response):
    get.return_value = response({"data": {"email": None}})
    assert HunterIOClient("key").generate_email("John", "Doe", "example.com") is None
    assert get.call_args.kwargs["params"]["last_name"] == "Doe"


@patch("src.utils.requests.get")
def test_not_found(get, response):
    get.return_value = response({}, 404)
    assert HunterIOClient("key").generate_email("John Doe", "example.com") is None


@pytest.mark.parametrize("payload", [{}, {"data": None}, {"data": {}},
                                     {"errors": ["failure"]}, {"data": {"email": []}}])
@patch("src.utils.requests.get")
def test_malformed_response(get, payload, response):
    get.return_value = response(payload)
    with pytest.raises(APIError):
        HunterIOClient("key").generate_email("John Doe", "example.com")
