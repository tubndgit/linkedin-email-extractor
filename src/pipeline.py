"""Contact enrichment with explicit verification and per-contact errors."""

from .utils import APIError


def enrich_contacts(contacts, hunter, neverbounce, anymailfinder=None, *,
                    anymailfinder_mode="fallback"):
    if anymailfinder_mode not in {"fallback", "always", "off"}:
        raise ValueError("Unknown AnyMailFinder mode")
    if anymailfinder_mode != "off" and anymailfinder is None:
        raise ValueError("AnyMailFinder client is required for this mode")
    results = []
    verification_cache = {}
    disabled = {}

    def call(provider, operation, *args):
        if provider in disabled:
            raise APIError(provider, f"skipped after HTTP {disabled[provider]}")
        try:
            return operation(*args)
        except APIError as error:
            # Account-wide failures should not be repeated for every contact.
            if error.status_code in {401, 402, 403, 429}:
                disabled[provider] = error.status_code
            raise

    for contact in contacts:
        record = {**contact, "emails": [], "errors": []}
        candidates = {}
        blocked = False

        def add_candidate(email, source):
            identity = email.casefold()
            if identity in candidates:
                if source not in candidates[identity]["sources"]:
                    candidates[identity]["sources"].append(source)
                return
            candidate = {"email": email, "sources": [source],
                         "verification": "error", "verified": False}
            candidates[identity] = candidate
            record["emails"].append(candidate)
            if identity not in verification_cache:
                try:
                    verification_cache[identity] = call(
                        "NeverBounce", neverbounce.verify_email, email)["result"]
                except APIError as error:
                    verification_cache[identity] = error
            verification = verification_cache[identity]
            if isinstance(verification, APIError):
                record["errors"].append(str(verification))
            else:
                candidate["verification"] = verification
                candidate["verified"] = verification == "valid"

        try:
            email = call("Hunter", hunter.generate_email, contact["name"], contact["domain"])
            if email:
                add_candidate(email, "hunter")
        except APIError as error:
            record["errors"].append(str(error))
            # Hunter's 451 is a removal request; do not seek another provider.
            blocked = error.status_code == 451

        has_verified = any(candidate["verified"] for candidate in record["emails"])
        if (not blocked and anymailfinder_mode != "off"
                and (anymailfinder_mode == "always" or not has_verified)):
            try:
                for email in call("AnyMailFinder", anymailfinder.find_additional_emails,
                                  contact["name"], contact["domain"]):
                    add_candidate(email, "anymailfinder")
            except APIError as error:
                record["errors"].append(str(error))
        if blocked:
            record["status"] = "blocked"
        elif any(candidate["verified"] for candidate in record["emails"]):
            record["status"] = "verified"
        elif record["errors"]:
            record["status"] = "error"
        elif record["emails"]:
            record["status"] = "unverified"
        else:
            record["status"] = "not_found"
        results.append(record)
    return results
