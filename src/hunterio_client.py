"""Hunter v2 Email Finder adapter."""

from .utils import APIError, handle_api_request, parse_email, validate_api_key, validate_timeout


class HunterIOClient:
    def __init__(self, api_key, *, timeout=180):
        self.api_key = validate_api_key(api_key)
        self.timeout = validate_timeout(timeout)
        self.base_url = "https://api.hunter.io/v2"

    def generate_email(self, first_name, last_name=None, domain=None):
        """Return an email or None; accept (full_name, domain) or three fields."""
        if domain is None:
            domain = last_name
            names = {"full_name": first_name}
        elif last_name is None:
            names = {"full_name": first_name}
        else:
            names = {"first_name": first_name, "last_name": last_name}
        data = handle_api_request(
            f"{self.base_url}/email-finder",
            params={**names, "domain": domain, "api_key": self.api_key},
            timeout=self.timeout, provider="Hunter", allow_not_found=True,
        )
        if data is None:
            return None
        if data.get("errors") or not isinstance(data.get("data"), dict):
            raise APIError("Hunter", "unsuccessful or malformed response")
        if "email" not in data["data"]:
            raise APIError("Hunter", "missing email field")
        return parse_email(data["data"]["email"], "Hunter")
