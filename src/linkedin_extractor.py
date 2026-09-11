"""Import contact records collected from Sales Navigator or a CRM.

This module does not log into or scrape LinkedIn. A direct Sales Navigator
integration must supply real records to extract_names_and_domains().
"""

import csv
import ipaddress
import json
from collections.abc import Mapping
from pathlib import Path
import re
from urllib.parse import urlsplit


def normalize_domain(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("a company domain or website is required")
    value = value.strip()
    if any(char.isspace() for char in value):
        raise ValueError("invalid company domain")
    try:
        parsed = urlsplit(value if "://" in value else "https://" + value)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            raise ValueError
        domain = (parsed.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
        # Trigger validation of malformed port numbers, even though ports are ignored.
        parsed.port
    except (ValueError, UnicodeError):
        raise ValueError("invalid company domain") from None
    if domain.startswith("www."):
        domain = domain[4:]
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("a company domain is required, not an IP address")
    labels = domain.split(".")
    if (len(domain) > 253 or len(labels) < 2 or labels[-1].isdigit()
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                   for label in labels)):
        raise ValueError("invalid company domain")
    return domain


class LinkedInExtractor:
    def extract_names_and_domains(self, source):
        """Read CSV/JSON or an iterable of mappings, validate, and deduplicate.

        Header aliases include Name / Full Name / First Name + Last Name and
        Domain / Company Domain / Website. Invalid rows fail before API calls.
        """
        if isinstance(source, (str, Path)):
            path = Path(source)
            with path.open(encoding="utf-8-sig", newline="") as handle:
                if path.suffix.lower() == ".csv":
                    source = list(csv.DictReader(handle))
                elif path.suffix.lower() == ".json":
                    source = json.load(handle)
                else:
                    raise ValueError("Input must be a .csv or .json file")
        if isinstance(source, (Mapping, str, bytes)) or source is None:
            raise ValueError("Input must contain a list of contact records")
        try:
            iterator = iter(source)
        except TypeError:
            raise ValueError("Input must contain a list of contact records") from None
        contacts, seen = [], set()
        for index, raw in enumerate(iterator, start=1):
            try:
                if not isinstance(raw, Mapping) or None in raw:
                    raise ValueError("expected a contact record with named columns")
                row = {str(key).strip().lower().replace(" ", "_"): value
                       for key, value in raw.items()}
                name = row.get("name") or row.get("full_name")
                if not name:
                    parts = [row.get("first_name") or "", row.get("last_name") or ""]
                    if not all(isinstance(part, str) for part in parts):
                        raise ValueError("name must be text")
                    name = " ".join(parts)
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("a name is required")
                name = " ".join(name.split())
                domain = normalize_domain(row.get("domain") or row.get("company_domain")
                                          or row.get("website"))
            except ValueError as error:
                raise ValueError(f"Contact {index}: {error}") from None
            identity = (name.casefold(), domain)
            if identity not in seen:
                contacts.append({"name": name, "domain": domain})
                seen.add(identity)
        return contacts
