"""NeverBounce v4 single-email verification."""

from .utils import APIError, handle_api_request, validate_api_key, validate_timeout


class NeverBounceClient:
    RESULTS = {"valid", "invalid", "disposable", "catchall", "unknown"}

    def __init__(self, api_key, *, timeout=180):
        self.api_key = validate_api_key(api_key)
        self.timeout = validate_timeout(timeout)
        self.base_url = "https://api.neverbounce.com/v4"

    def verify_email(self, email):
        """Return the result object; only result == 'valid' is verified."""
        data = handle_api_request(
            f"{self.base_url}/single/check",
            params={"key": self.api_key, "email": email},
            timeout=self.timeout, provider="NeverBounce",
        )
        if data.get("status") != "success":
            raise APIError("NeverBounce", "verification request was unsuccessful")
        if not isinstance(data.get("result"), str) or data["result"] not in self.RESULTS:
            raise APIError("NeverBounce", "missing or unrecognized verification result")
        return data
