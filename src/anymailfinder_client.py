"""Anymail Finder v5.1 person lookup."""

from .utils import APIError, handle_api_request, parse_email, validate_api_key, validate_timeout


class AnyMailFinderClient:
    def __init__(self, api_key, *, timeout=180):
        self.api_key = validate_api_key(api_key)
        self.timeout = validate_timeout(timeout)
        self.base_url = "https://api.anymailfinder.com/v5.1"

    def find_additional_emails(self, name, domain):
        data = handle_api_request(
            f"{self.base_url}/find-email/person", method="POST",
            params={"full_name": name, "domain": domain},
            headers={"Authorization": self.api_key},
            timeout=self.timeout, provider="AnyMailFinder",
        )
        status = data.get("email_status")
        if data.get("error") or status not in ("valid", "risky", "not_found", "blacklisted"):
            raise APIError("AnyMailFinder", "unsuccessful or malformed response")
        if status in ("not_found", "blacklisted"):
            return []
        email = parse_email(data.get("email"), "AnyMailFinder")
        if email is None:
            raise APIError("AnyMailFinder", "missing email for a matched result")
        # Risky matches still go through NeverBounce before being accepted.
        return [email]
