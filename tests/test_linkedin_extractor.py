import json

import pytest

from src.linkedin_extractor import LinkedInExtractor, normalize_domain


@pytest.mark.parametrize("domain,expected", [
    ("https://www.Example.com/about?q=1", "example.com"),
    (" Example.com. ", "example.com"), ("mail.example.co.uk", "mail.example.co.uk"),
    ("bücher.de", "xn--bcher-kva.de"),
])
def test_domain_normalization(domain, expected):
    assert normalize_domain(domain) == expected


@pytest.mark.parametrize("domain", [None, "", "invalid_domain", "localhost", "-bad.com",
                                    "user@example.com", "127.0.0.1", "https://[::1]",
                                    "ftp://example.com", "example .com", "example.com:bad"])
def test_invalid_domains(domain):
    with pytest.raises(ValueError):
        normalize_domain(domain)


def test_normalize_aliases_and_deduplicate():
    result = LinkedInExtractor().extract_names_and_domains([
        {"First Name": "John", "Last Name": "van Doe", "Website": "https://www.Example.com/about"},
        {"name": " john  VAN Doe ", "domain": "example.com"},
        {"Full Name": "Jane Smith", "Company Domain": "example.com"},
    ])
    assert result == [{"name": "John van Doe", "domain": "example.com"},
                      {"name": "Jane Smith", "domain": "example.com"}]


@pytest.mark.parametrize("extension", ["csv", "json"])
def test_file_input(tmp_path, extension):
    path = tmp_path / f"contacts.{extension}"
    path.write_text("\ufeffname,domain\nJohn Doe,example.com\n" if extension == "csv" else
                    json.dumps([{"name": "John Doe", "domain": "example.com"}]), encoding="utf-8")
    assert LinkedInExtractor().extract_names_and_domains(path) == [{"name": "John Doe", "domain": "example.com"}]


@pytest.mark.parametrize("records", [[{"name": "John"}], [{"domain": "example.com"}],
                                     [None], {"name": "John"}, None, 123,
                                     [{"first_name": ["John"], "domain": "example.com"}]])
def test_bad_input(records):
    with pytest.raises(ValueError):
        LinkedInExtractor().extract_names_and_domains(records)


def test_extra_csv_columns_rejected(tmp_path):
    path = tmp_path / "contacts.csv"
    path.write_text("name,domain\nJohn,example.com,extra\n")
    with pytest.raises(ValueError, match="Contact 1"):
        LinkedInExtractor().extract_names_and_domains(path)


def test_no_fabricated_contacts():
    assert LinkedInExtractor().extract_names_and_domains([]) == []
