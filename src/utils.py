"""HTTP helpers shared by the paid email providers."""

import json
import logging
import math

import requests


class APIError(RuntimeError):
    """A safe provider error that never includes URLs, API keys, or payloads."""

    def __init__(self, provider, message, status_code=None):
        super().__init__(f"{provider}: {message}")
        self.status_code = status_code


def validate_api_key(api_key):
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("A nonempty API key is required")
    return api_key.strip()


def validate_timeout(timeout):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ValueError("Request timeout must be a positive number")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Request timeout must be a positive number")
    return timeout


def handle_api_request(url, params=None, method="GET", *, headers=None,
                       timeout=180, provider="Email API", allow_not_found=False):
    """Make one request; do not automatically retry potentially billable calls."""
    validate_timeout(timeout)
    method = method.upper()
    if method not in {"GET", "POST"}:
        raise ValueError(f"Unsupported HTTP method: {method}")
    try:
        # Avoid forwarding credentials through an unexpected redirect.
        kwargs = {"timeout": (5, timeout), "allow_redirects": False}
        if headers is not None:
            kwargs["headers"] = headers
        if method == "GET":
            response = requests.get(url, params=params, **kwargs)
        else:
            response = requests.post(url, json=params, **kwargs)
    except requests.Timeout:
        raise APIError(provider, "request timed out") from None
    except requests.RequestException:
        raise APIError(provider, "connection failed") from None

    if allow_not_found and response.status_code == 404:
        return None
    if not 200 <= response.status_code < 300:
        raise APIError(provider, f"HTTP {response.status_code}", response.status_code)
    try:
        payload = response.json()
    except ValueError:
        raise APIError(provider, "invalid JSON response") from None
    if not isinstance(payload, dict):
        raise APIError(provider, "expected a JSON object")
    return payload


def parse_email(value, provider):
    """Distinguish a missing match from a malformed provider response."""
    if value is None:
        return None
    if not isinstance(value, str) or value.count("@") != 1:
        raise APIError(provider, "invalid email in response")
    email = value.strip()
    local, domain = email.split("@")
    if not local or not domain or any(c.isspace() for c in email):
        raise APIError(provider, "invalid email in response")
    return email


def log_message(message):
    logging.getLogger(__name__).info(message)


def format_data(data):
    return json.dumps(data, indent=2, ensure_ascii=False)
