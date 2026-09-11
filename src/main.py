"""Command-line entry point: python -m src.main --input contacts.csv."""

import argparse
import csv
import json
import os
from pathlib import Path
import sys
import tempfile

# Retain the original `python src/main.py` entry point as well as module usage.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.anymailfinder_client import AnyMailFinderClient
from src.config import DEFAULT_CONFIG, load_config
from src.hunterio_client import HunterIOClient
from src.linkedin_extractor import LinkedInExtractor
from src.neverbounce_client import NeverBounceClient
from src.pipeline import enrich_contacts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find and verify emails from contact CSV/JSON files.")
    parser.add_argument("--input", required=True, type=Path, help="Contact CSV or JSON file")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=Path("output/results.json"))
    parser.add_argument("--dry-run", action="store_true", help="Validate input without API calls or keys")
    parser.add_argument("--anymailfinder", choices=["fallback", "always", "off"], default="fallback",
                        help="Search when Hunter has no verified match (default), always, or never")
    args = parser.parse_args(argv)
    temporary_path = None
    try:
        if args.output.resolve() in {args.input.resolve(), args.config.resolve()}:
            raise ValueError("Output must be different from input and configuration")
        contacts = LinkedInExtractor().extract_names_and_domains(args.input)
        if not contacts:
            raise ValueError("Input contains no contacts")
        config = None if args.dry_run else load_config(
            args.config, use_anymailfinder=args.anymailfinder != "off")
        # Check output access before spending API credits; replace it atomically.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists() and not args.output.is_file():
            raise ValueError("Output must be a file")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent,
                                         prefix=".email-results-", suffix=".json", delete=False) as handle:
            temporary_path = Path(handle.name)
            if args.dry_run:
                report = {"dry_run": True, "contact_count": len(contacts), "contacts": contacts}
                has_errors = False
            else:
                keys, timeout = config["api_keys"], config["request_timeout"]
                results = enrich_contacts(
                    contacts,
                    HunterIOClient(keys["hunter_io"], timeout=timeout),
                    NeverBounceClient(keys["neverbounce"], timeout=timeout),
                    AnyMailFinderClient(keys["anymailfinder"], timeout=timeout)
                    if args.anymailfinder != "off" else None,
                    anymailfinder_mode=args.anymailfinder,
                )
                verified_by_address = {}
                for result in results:
                    for candidate in result["emails"]:
                        if candidate["verified"]:
                            email = candidate["email"]
                            verified_by_address.setdefault(email.casefold(), email)
                verified = sorted(verified_by_address.values(), key=str.casefold)
                has_errors = any(result["errors"] for result in results)
                report = {"dry_run": False, "contact_count": len(contacts),
                          "verified_emails": verified, "results": results}
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary_path, args.output)
        temporary_path = None
        print(f"{'Validated' if args.dry_run else 'Processed'} {len(contacts)} contacts. "
              f"Saved {args.output}")
        if has_errors:
            print("Some provider requests failed; see errors in the saved results.", file=sys.stderr)
        return 2 if has_errors else 0
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
