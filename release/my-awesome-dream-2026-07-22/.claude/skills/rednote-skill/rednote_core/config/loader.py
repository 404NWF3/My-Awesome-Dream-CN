"""Configuration loader — reads YAML config files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import yaml

DEFAULT_CONFIG = {
    "client": {
        "proxy": None,
        "timeout": 30,
        "retry_interval": 5,
        "request_interval": 2,
    },
    "auth": {
        "cookies_file": "config/cookies.enc",
    },
    "output": {
        "reports_dir": "data/reports",
        "default_format": "html",
    },
}


def load_config(path: str | None = None) -> dict[str, Any]:
    """Load configuration from YAML file, merging with defaults."""
    if path is None:
        candidates = [
            "config/settings.yaml",
            os.path.expanduser("~/.rednote/config.yaml"),
        ]
        for c in candidates:
            if os.path.exists(c):
                path = c
                break

    config = dict(DEFAULT_CONFIG)

    if path and os.path.exists(path):
        with open(path) as f:
            file_config = yaml.safe_load(f) or {}
        _deep_merge(config, file_config)

    return config


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override into base (mutates base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
