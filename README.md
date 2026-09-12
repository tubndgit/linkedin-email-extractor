# LinkedIn Email Extractor

This project is designed to extract names and domains from LinkedIn Sales Navigator accounts, generate emails using the Hunter IO API, verify emails with the NeverBounce API, and find additional emails using [AnyMailFinder](https://anymailfinder.com?via=henry-b).

## Current capabilities

The enrichment pipeline works with contact records supplied as CSV or JSON.
**Direct login, scraping, and extraction from Sales Navigator are not implemented.**
The previous extractor returned a hard-coded example contact; it now requires real
input. Supply records from your existing export/CRM workflow, or feed mappings
from a future Sales Navigator integration to `LinkedInExtractor`.

For each contact, the application:

1. Validates the name and normalizes the company domain (including website URLs).
2. Removes duplicate name/domain pairs before paid requests.
3. Finds an email with Hunter and verifies it with NeverBounce.
4. Uses [AnyMailFinder](https://anymailfinder.com?via=henry-b) when no verified email is available, or for every contact
   with `--anymailfinder always`. Its candidates also pass through NeverBounce.
5. Saves a JSON report with candidates, provider sources, verification outcomes,
   per-contact errors, and a separate `verified_emails` list.

Only NeverBounce's `valid` result is accepted. `invalid`, `catchall`, `disposable`,
and `unknown` remain unverified. Duplicate email candidates share a verification
result within a run, including failures. Rerunning a file starts a new run and may
consume credits again; there is no persistent cache or resume support.

## Setup

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create an [AnyMailFinder account](https://anymailfinder.com?via=henry-b) (affiliate link)
and get your API key from its dashboard. Set your provider API keys in the environment:

```sh
export HUNTER_API_KEY='your-hunter-key'
export NEVERBOUNCE_API_KEY='your-neverbounce-key'
export ANYMAILFINDER_API_KEY='your-anymailfinder-key'
```

Environment variables take precedence over `api_keys.hunter_io`,
`api_keys.neverbounce`, and `api_keys.anymailfinder` in the YAML configuration.
The tracked `config/config.yaml` contains blank values. For personal YAML settings,
copy it to `config/config.local.yaml` (ignored by Git) and pass
`--config config/config.local.yaml`. `.env` files are not loaded automatically.
[AnyMailFinder](https://anymailfinder.com?via=henry-b)'s key is unnecessary when using `--anymailfinder off`.

The default configuration path is relative to the project, so it works when
invoking the script from another directory. Input/output paths are relative to
your current directory. Provider URLs are fixed in their adapters; the scaffold's
unused `endpoints` configuration has been removed.

## Input and usage

Create a CSV file with these columns:

```csv
name,domain
John Doe,example.com
Jane Smith,https://www.example.org/about
```

JSON accepts a list of objects with the same fields. Header aliases include
`Full Name`, `First Name` + `Last Name`, `Company Domain`, and `Website`.
Names retain their full spelling; company names alone are not converted to domains.
Malformed contacts stop the run before any API calls.

Validate the included sample without API keys or network requests:

```sh
python -m src.main --input examples/contacts.csv --dry-run --output output/preview.json
```

Enrich your own contacts:

```sh
python -m src.main --input contacts/leads.csv --output output/results.json
```

Search [AnyMailFinder](https://anymailfinder.com?via=henry-b) even when Hunter found a verified email:

```sh
python -m src.main --input contacts/leads.csv --anymailfinder always
```

`python src/main.py` is also supported with the same arguments. `--input` is
required. Use `--help` for all options. The default output is `output/results.json`;
a successful run replaces an existing output file atomically. Reports contain
contact data; keep local inputs in the ignored `contacts/` directory and outputs
in the ignored `output/` directory.

The program returns exit code `0` for a completed run or successful dry run,
`1` for input/configuration/output errors, and `2` when provider errors occurred
(the report is still saved). A completed run can contain no verified emails;
check `verified_emails` or each contact's `status` before using results.

## Failure handling

Requests have a five-second connection timeout and a configurable read timeout
(default 180 seconds). They are not automatically retried, to avoid repeating
potentially billable calls after an uncertain response. Redirects are rejected.

HTTP, timeout, malformed-response, and provider errors are recorded without
including credentials, response bodies, or full request URLs. Other contacts
continue processing. After HTTP 401/402/403/429, the affected provider is skipped
for the rest of that run. A Hunter HTTP 451 removal response stops enrichment for
that contact, including fallback. Provider failures are distinct from a genuine
no-match result. Results are saved when the batch finishes; interruption before
completion does not save the in-progress batch.

## Development and testing

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests mock the HTTP boundary and block unmocked requests. They cover provider
request/response contracts, input normalization, duplicate handling, verification
rules, fallback, failures, configuration, and the CLI. No API credits or live
accounts are needed. Live account integrations still need a smoke test with your
own credentials before production use.

## Provider references

Adapters follow the [Hunter v2 Email Finder reference](https://hunter.io/api-documentation/v2),
[NeverBounce single-check reference](https://developers.neverbounce.com/v4/reference/single-check),
and [AnyMailFinder person-search reference](https://anymailfinder.com/email-finder-api/docs/find-person-email)
with its [authentication format](https://anymailfinder.com/email-finder-api/docs/authentication).

## Project structure

- `src/linkedin_extractor.py`: CSV/JSON ingestion and contact normalization.
- `src/hunterio_client.py`, `src/neverbounce_client.py`, `src/anymailfinder_client.py`: provider adapters.
- `src/pipeline.py`: enrichment, fallback, deduplication, and verification.
- `src/config.py`: configuration and environment validation.
- `src/utils.py`: shared HTTP handling and safe errors.
- `src/main.py`: CLI and JSON output.
- `tests/`: offline regression and integration tests.

## License

This project is licensed under the [MIT License](LICENSE).
