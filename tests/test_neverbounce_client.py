from unittest.mock import patch

import pytest

from src.neverbounce_client import NeverBounceClient
from src.utils import APIError


@pytest.mark.parametrize("result", ["valid", "invalid", "catchall", "unknown", "disposable"])
@patch("src.utils.requests.get")
def test_verification_results(get, result, response):
    get.return_value = response({"status": "success", "result": result})
    assert NeverBounceClient("secret").verify_email("john+tag@example.com")["result"] == result
    get.assert_called_once_with(
        "https://api.neverbounce.com/v4/single/check",
        params={"key": "secret", "email": "john+tag@example.com"},
        timeout=(5, 180), allow_redirects=False,
    )


@pytest.mark.parametrize("payload", [{"status": "auth_failure", "result": "valid"},
                                     {"result": "valid"}, {"status": "success"},
                                     {"status": "success", "result": []},
                                     {"status": "success", "result": "new_status"}])
@patch("src.utils.requests.get")
def test_unsuccessful_verification(get, payload, response):
    get.return_value = response(payload)
    with pytest.raises(APIError):
        NeverBounceClient("key").verify_email("john@example.com")
