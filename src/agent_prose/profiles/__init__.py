"""Dialect profile registry and resolution cascade for agent-prose."""
from __future__ import annotations

import json
import locale
import os
from pathlib import Path
from typing import Dict

from agent_prose.profiles.base import DialectProfile
from agent_prose.profiles.en_au import PROFILE_EN_AU
from agent_prose.profiles.en_gb import PROFILE_EN_GB
from agent_prose.profiles.en_us import PROFILE_EN_US

PROFILE_REGISTRY: Dict[str, DialectProfile] = {
    "en-au": PROFILE_EN_AU,
    "en_au": PROFILE_EN_AU,
    "australia": PROFILE_EN_AU,
    "au": PROFILE_EN_AU,
    "en-us": PROFILE_EN_US,
    "en_us": PROFILE_EN_US,
    "american": PROFILE_EN_US,
    "us": PROFILE_EN_US,
    "en-gb": PROFILE_EN_GB,
    "en_gb": PROFILE_EN_GB,
    "british": PROFILE_EN_GB,
    "uk": PROFILE_EN_GB,
}

DEFAULT_LOCALE = "en-US"


def get_profile(name_or_code: str) -> DialectProfile:
    """Retrieve a profile by code or name; fallback to DEFAULT_LOCALE if not found."""
    normalized = name_or_code.strip().lower().replace("_", "-")
    if normalized in PROFILE_REGISTRY:
        return PROFILE_REGISTRY[normalized]
    # Check prefixes like 'en'
    if normalized.startswith("en-au") or normalized == "au":
        return PROFILE_EN_AU
    if normalized.startswith("en-gb") or normalized in ("gb", "uk"):
        return PROFILE_EN_GB
    if normalized.startswith("en-us") or normalized == "us":
        return PROFILE_EN_US
    return PROFILE_REGISTRY[DEFAULT_LOCALE.lower()]


def _find_config_locale() -> str | None:
    """Search current directory and parents for .proserc.json or pyproject.toml."""
    curr = Path.cwd()
    for directory in [curr, *curr.parents]:
        proserc = directory / ".proserc.json"
        if proserc.is_file():
            try:
                with open(proserc, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "locale" in data:
                        return str(data["locale"])
            except Exception:
                pass
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            try:
                # Basic string extraction without requiring tomli/tomllib
                with open(pyproject, "r", encoding="utf-8") as f:
                    content = f.read()
                    import re
                    m = re.search(r'(?:\[tool\.agent[-_]prose\][^\[]*locale\s*=\s*["\']([^"\']+)["\'])', content)
                    if m:
                        return m.group(1)
            except Exception:
                pass
    return None


def resolve_locale(cli_override: str | None = None) -> DialectProfile:
    """Resolve active profile through 5-stage priority cascade.

    1. CLI argument override
    2. Project configuration (.proserc.json or pyproject.toml)
    3. Environment variable (AGENT_PROSE_LOCALE or PROSE_LOCALE)
    4. Host operating system locale
    5. Baseline default (en-US)
    """
    # 1. CLI override
    if cli_override and cli_override.strip():
        return get_profile(cli_override)

    # 2. Project configuration
    cfg_locale = _find_config_locale()
    if cfg_locale:
        return get_profile(cfg_locale)

    # 3. Environment variable
    env_locale = os.environ.get("AGENT_PROSE_LOCALE") or os.environ.get("PROSE_LOCALE")
    if env_locale:
        return get_profile(env_locale)

    # 4. Host OS locale detection
    try:
        os_loc = locale.getlocale()[0]
        if not os_loc and hasattr(locale, "getdefaultlocale"):
            os_loc = locale.getdefaultlocale()[0]
        if os_loc:
            return get_profile(os_loc)
    except Exception:
        pass

    # 5. Baseline fallback
    return get_profile(DEFAULT_LOCALE)


__all__ = [
    "DialectProfile",
    "PROFILE_REGISTRY",
    "get_profile",
    "resolve_locale",
    "DEFAULT_LOCALE",
]
