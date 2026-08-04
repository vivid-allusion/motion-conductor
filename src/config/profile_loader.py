"""Load and normalize profile YAML configuration."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any


def normalize_legacy_profile(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize old profile formats (Model, duration_config) to Engine-interface keys."""
    if "Model" in data and "endpoint" not in data:
        data["endpoint"] = data["Model"].get("endpoint", "")

    if "platform" not in data:
        data["platform"] = "replicate"

    if "media_type" not in data:
        data["media_type"] = "video"

    if "duration_config" in data and "parameters" not in data:
        dc = data.get("duration_config", {})
        if dc:
            data["parameters"] = {"fps": dc.get("fps", 24)}
    elif "parameters" not in data:
        data["parameters"] = {}

    params = data.get("parameters", {})
    if "fps" not in params:
        params["fps"] = 24

    return data


def load_profile_standalone() -> dict[str, Any]:
    """Load profile from USER-FILES for standalone mode, normalize format."""
    profiles_dir = Path("USER-FILES/03.PROFILES")
    yamls = sorted(profiles_dir.glob("*.yaml")) + sorted(profiles_dir.glob("*.yml"))
    if not yamls:
        standby = Path("USER-FILES/02.STANDBY")
        yamls = sorted(standby.glob("*.yaml")) + sorted(standby.glob("*.yml"))
    if not yamls:
        raise FileNotFoundError(
            "No profile found in USER-FILES/03.PROFILES/ or USER-FILES/02.STANDBY/"
        )

    data = yaml.safe_load(yamls[0].read_text(encoding="utf-8")) or {}
    data = normalize_legacy_profile(data)
    data["profile_name"] = yamls[0].stem
    return data


def load_profile_studiolot(profile_path: Path) -> dict[str, Any]:
    """Load profile YAML from --profile flag."""
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    data["profile_name"] = profile_path.stem
    return data
