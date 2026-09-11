from unittest.mock import Mock, patch

import pytest

from src.anymailfinder_client import AnyMailFinderClient
from src.hunterio_client import HunterIOClient
from src.neverbounce_client import NeverBounceClient
from src.pipeline import enrich_contacts
from src.utils import APIError

CONTACTS = [{"name": "John Doe", "domain": "example.com"}]


def clients():
    hunter, verifier, finder = Mock(), Mock(), Mock()
    hunter.generate_email.return_value = "john@example.com"
    verifier.verify_email.return_value = {"status": "success", "result": "valid"}
    finder.find_additional_emails.return_value = ["other@example.com"]
    return hunter, verifier, finder


@pytest.mark.parametrize("result", ["invalid", "catchall", "unknown", "disposable"])
def test_non_valid_results_are_never_accepted(result):
    hunter, verifier, finder = clients()
    verifier.verify_email.return_value = {"result": result}
    report = enrich_contacts(CONTACTS, hunter, verifier, finder)
    assert report[0]["status"] == "unverified"
    assert all(not email["verified"] for email in report[0]["emails"])
    assert verifier.verify_email.call_count == 2
    finder.find_additional_emails.assert_called_once_with("John Doe", "example.com")


def test_valid_hunter_skips_fallback():
    hunter, verifier, finder = clients()
    assert enrich_contacts(CONTACTS, hunter, verifier, finder)[0]["status"] == "verified"
    finder.find_additional_emails.assert_not_called()


def test_missing_hunter_match_uses_and_verifies_fallback():
    hunter, verifier, finder = clients()
    hunter.generate_email.return_value = None
    report = enrich_contacts(CONTACTS, hunter, verifier, finder)
    assert report[0]["emails"][0]["verified"] is True
    verifier.verify_email.assert_called_once_with("other@example.com")


def test_always_mode_merges_sources_and_caches_across_contacts():
    hunter, verifier, finder = clients()
    finder.find_additional_emails.return_value = ["JOHN@example.com"]
    report = enrich_contacts(CONTACTS + [{"name": "J Doe", "domain": "example.com"}],
                             hunter, verifier, finder, anymailfinder_mode="always")
    assert report[0]["emails"][0]["sources"] == ["hunter", "anymailfinder"]
    assert len(report[0]["emails"]) == 1
    assert report[1]["emails"][0]["verified"] is True
    verifier.verify_email.assert_called_once()


def test_verification_error_is_not_valid_and_does_not_abort_batch():
    hunter, verifier, finder = clients()
    verifier.verify_email.side_effect = APIError("NeverBounce", "request timed out")
    report = enrich_contacts(CONTACTS * 2, hunter, verifier, finder)
    assert len(report) == 2
    assert all(row["status"] == "error" and row["errors"] for row in report)
    assert all(not email["verified"] for row in report for email in row["emails"])
    assert verifier.verify_email.call_count == 2  # One per unique address, including failed checks.


@pytest.mark.parametrize("status", [401, 402, 403, 429])
def test_account_errors_stop_repeated_calls(status):
    hunter, verifier, finder = clients()
    hunter.generate_email.side_effect = APIError("Hunter", f"HTTP {status}", status)
    report = enrich_contacts(CONTACTS * 2, hunter, verifier, finder)
    hunter.generate_email.assert_called_once()
    assert f"skipped after HTTP {status}" in report[1]["errors"][0]
    assert all(row["status"] == "verified" for row in report)


def test_provider_removal_response_does_not_trigger_fallback():
    hunter, verifier, finder = clients()
    hunter.generate_email.side_effect = APIError("Hunter", "HTTP 451", 451)
    assert enrich_contacts(CONTACTS, hunter, verifier, finder)[0]["status"] == "blocked"
    finder.find_additional_emails.assert_not_called()
    verifier.verify_email.assert_not_called()


def test_no_matches():
    hunter, verifier, finder = clients()
    hunter.generate_email.return_value = None
    finder.find_additional_emails.return_value = []
    assert enrich_contacts(CONTACTS, hunter, verifier, finder)[0]["status"] == "not_found"
    verifier.verify_email.assert_not_called()


@patch("src.utils.requests.post")
@patch("src.utils.requests.get")
def test_real_adapters_in_pipeline(get, post, response):
    get.side_effect = [response({"data": {"email": "bad@example.com"}}),
                       response({"status": "success", "result": "invalid"}),
                       response({"status": "success", "result": "valid"})]
    post.return_value = response({"email": "good@example.com", "email_status": "valid"})
    report = enrich_contacts(CONTACTS, HunterIOClient("h"), NeverBounceClient("n"), AnyMailFinderClient("a"))
    assert [email["verified"] for email in report[0]["emails"]] == [False, True]
    assert report[0]["status"] == "verified"
