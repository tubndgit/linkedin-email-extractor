import json
from unittest.mock import patch

import pytest

from src.config import load_config
from src.main import main


@pytest.fixture
def input_file(tmp_path):
    path = tmp_path / "contacts.csv"
    path.write_text("name,domain\nJohn Doe,https://www.example.com/about\n")
    return path


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    for variable in ("HUNTER_API_KEY", "NEVERBOUNCE_API_KEY", "ANYMAILFINDER_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    path = tmp_path / "config.yaml"
    path.write_text("api_keys:\n  hunter_io: h\n  neverbounce: n\n  anymailfinder: a\n")
    return path


def test_env_overrides_yaml(config_file, monkeypatch):
    monkeypatch.setenv("HUNTER_API_KEY", "override")
    assert load_config(config_file)["api_keys"]["hunter_io"] == "override"


@pytest.mark.parametrize("value", ["''", "YOUR_HUNTER_API_KEY", "123", "null"])
def test_bad_key(config_file, value):
    config_file.write_text(f"api_keys:\n  hunter_io: {value}\n")
    with pytest.raises(ValueError, match="HUNTER_API_KEY"):
        load_config(config_file)


def test_disabled_finder_does_not_require_key(config_file):
    config_file.write_text("api_keys:\n  hunter_io: h\n  neverbounce: n\n")
    assert "anymailfinder" not in load_config(config_file, use_anymailfinder=False)["api_keys"]


@pytest.mark.parametrize("timeout", ["0", "-1", "true", ".nan", ".inf", "'180'"])
def test_bad_timeout(config_file, timeout):
    with config_file.open("a") as handle:
        handle.write(f"request_timeout: {timeout}\n")
    with pytest.raises(ValueError, match="timeout"):
        load_config(config_file)


def test_malformed_yaml_does_not_expose_key(config_file):
    config_file.write_text("api_keys: [secret: [")
    with pytest.raises(ValueError) as error:
        load_config(config_file)
    assert "secret" not in str(error.value)


def test_dry_run_requires_no_config_or_network(input_file, tmp_path):
    output = tmp_path / "results.json"
    assert main(["--input", str(input_file), "--output", str(output), "--dry-run",
                 "--config", str(tmp_path / "missing.yaml")]) == 0
    report = json.loads(output.read_text())
    assert report == {"dry_run": True, "contact_count": 1,
                      "contacts": [{"name": "John Doe", "domain": "example.com"}]}


@patch("src.utils.requests.get")
def test_cli_saves_real_pipeline_results(get, input_file, config_file, tmp_path, response):
    get.side_effect = [response({"data": {"email": "john@example.com"}}),
                       response({"status": "success", "result": "valid"})]
    output = tmp_path / "results.json"
    assert main(["--input", str(input_file), "--config", str(config_file), "--output", str(output)]) == 0
    report = json.loads(output.read_text())
    assert report["verified_emails"] == ["john@example.com"]
    assert report["results"][0]["status"] == "verified"
    assert not list(tmp_path.glob(".email-results-*"))


@patch("src.utils.requests.get")
def test_partial_failure_saved_with_nonzero_exit(get, input_file, config_file, tmp_path, response):
    get.return_value = response({}, 401)
    output = tmp_path / "results.json"
    assert main(["--input", str(input_file), "--config", str(config_file),
                 "--output", str(output), "--anymailfinder", "off"]) == 2
    report = json.loads(output.read_text())
    assert report["verified_emails"] == []
    assert report["results"][0]["errors"] == ["Hunter: HTTP 401"]


def test_invalid_later_contact_prevents_any_paid_calls(input_file, config_file, tmp_path):
    with input_file.open("a") as handle:
        handle.write("Jane,not_a_domain\n")
    output = tmp_path / "results.json"
    assert main(["--input", str(input_file), "--config", str(config_file), "--output", str(output)]) == 1
    assert not output.exists()


def test_cannot_overwrite_input(input_file):
    original = input_file.read_text()
    assert main(["--input", str(input_file), "--output", str(input_file), "--dry-run"]) == 1
    assert input_file.read_text() == original


def test_unwritable_output_prevents_paid_calls(input_file, config_file, tmp_path):
    assert main(["--input", str(input_file), "--config", str(config_file),
                 "--output", str(tmp_path)]) == 1


@patch("src.utils.requests.get")
def test_verified_summary_deduplicates_case(get, input_file, config_file, tmp_path, response):
    with input_file.open("a") as handle:
        handle.write("J Doe,example.com\n")
    get.side_effect = [response({"data": {"email": "John@example.com"}}),
                       response({"status": "success", "result": "valid"}),
                       response({"data": {"email": "JOHN@example.com"}})]
    output = tmp_path / "results.json"
    assert main(["--input", str(input_file), "--config", str(config_file),
                 "--output", str(output), "--anymailfinder", "off"]) == 0
    assert json.loads(output.read_text())["verified_emails"] == ["John@example.com"]
    assert get.call_count == 3
