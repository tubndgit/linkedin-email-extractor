from unittest.mock import patch

import pytest
import requests

from src.utils import APIError, handle_api_request


@pytest.mark.parametrize("exception,message", [
    (requests.Timeout("secret in URL"), "timed out"),
    (requests.ConnectionError("secret in URL"), "connection failed"),
])
@patch("src.utils.requests.get")
def test_network_error_is_sanitized_and_not_retried(get, exception, message):
    get.side_effect = exception
    with pytest.raises(APIError, match=message) as error:
        handle_api_request("https://example.com", provider="Hunter")
    assert "secret" not in str(error.value)
    get.assert_called_once()


@pytest.mark.parametrize("status", [301, 401, 402, 403, 404, 429, 500, 503])
@patch("src.utils.requests.get")
def test_http_errors(get, status, response):
    get.return_value = response({"message": "secret"}, status)
    with pytest.raises(APIError, match=f"HTTP {status}") as error:
        handle_api_request("https://example.com")
    assert error.value.status_code == status
    assert "secret" not in str(error.value)
    get.assert_called_once()


@patch("src.utils.requests.get")
def test_bad_json(get, response):
    get.return_value = response(None)
    get.return_value.json.side_effect = ValueError("secret")
    with pytest.raises(APIError, match="invalid JSON"):
        handle_api_request("https://example.com")


@pytest.mark.parametrize("payload", [None, [], "ok", 1])
@patch("src.utils.requests.get")
def test_non_object_json(get, payload, response):
    get.return_value = response(payload)
    with pytest.raises(APIError, match="JSON object"):
        handle_api_request("https://example.com")
