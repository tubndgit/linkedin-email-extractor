from unittest.mock import patch

import pytest

from src.anymailfinder_client import AnyMailFinderClient
from src.utils import APIError


@pytest.mark.parametrize("status", ["valid", "risky"])
@patch("src.utils.requests.post")
def test_person_search(post, status, response):
    post.return_value = response({"email": "john@example.com", "email_status": status})
    assert AnyMailFinderClient("secret").find_additional_emails("John Doe", "example.com") == ["john@example.com"]
    post.assert_called_once_with(
        "https://api.anymailfinder.com/v5.1/find-email/person",
        json={"full_name": "John Doe", "domain": "example.com"},
        headers={"Authorization": "secret"}, timeout=(5, 180), allow_redirects=False,
    )


@pytest.mark.parametrize("status", ["not_found", "blacklisted"])
@patch("src.utils.requests.post")
def test_no_match(post, status, response):
    post.return_value = response({"email": None, "email_status": status})
    assert AnyMailFinderClient("key").find_additional_emails("John Doe", "example.com") == []


@pytest.mark.parametrize("payload", [{}, {"email_status": "valid", "email": None},
                                     {"email_status": "new_status"},
                                     {"email_status": "valid", "email": "bad"}])
@patch("src.utils.requests.post")
def test_malformed_response(post, payload, response):
    post.return_value = response(payload)
    with pytest.raises(APIError):
        AnyMailFinderClient("key").find_additional_emails("John Doe", "example.com")
