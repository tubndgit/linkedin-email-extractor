"""Validated configuration, with environment variables taking precedence."""

import os
from pathlib import Path

import yaml

from .utils import validate_timeout

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
KEY_VARIABLES = {
    "hunter_io": "HUNTER_API_KEY",
    "neverbounce": "NEVERBOUNCE_API_KEY",
    "anymailfinder": "ANYMAILFINDER_API_KEY",
}


def load_config(path=DEFAULT_CONFIG, *, use_anymailfinder=True):
    try:
        with Path(path).open(encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except yaml.YAMLError:
        # YAML parser exceptions may quote lines containing credentials.
        raise ValueError("Configuration is not valid YAML") from None
    if not isinstance(config, dict) or not isinstance(config.get("api_keys", {}), dict):
        raise ValueError("Configuration must contain an api_keys mapping")
    keys = {}
    for provider, variable in KEY_VARIABLES.items():
        if provider == "anymailfinder" and not use_anymailfinder:
            continue
        value = os.environ.get(variable, config.get("api_keys", {}).get(provider))
        if (not isinstance(value, str) or not value.strip()
                or value.strip().upper().startswith(("YOUR_", "REPLACE_"))):
            raise ValueError(f"Set {variable} to a real API key")
        keys[provider] = value.strip()
    return {"api_keys": keys,
            "request_timeout": validate_timeout(config.get("request_timeout", 180))}
