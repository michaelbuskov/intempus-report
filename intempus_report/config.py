"""Config loading and creation for intempus-report."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "intempus" / "config.toml"

DEFAULT_CONFIG_TEMPLATE = """\
[auth]
base_url = "https://intempus.dk"
username = "your@email.com"
password = "yourpassword"

# Optional: bonus calculation
# List the project names that count towards your bonus.
# Bonus is earned on hours above min_hours: (bonus_hours - min_hours) * (hourly_rate / 2)
#
# [bonus]
# hourly_rate = 1000.0   # rate paid by customer (same currency as your salary)
# min_hours   = 120.0    # threshold — bonus only on hours above this
# projects = [
#   "Project A",
#   "Project B",
# ]
"""


@dataclass
class AuthConfig:
    base_url: str
    username: str
    password: str


@dataclass
class BonusConfig:
    hourly_rate: float
    projects: list[str] = field(default_factory=list)
    min_hours: float = 0.0  # hours that must be exceeded before bonus kicks in


@dataclass
class Config:
    auth: AuthConfig
    bonus: BonusConfig | None = None


def _create_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_TEMPLATE)
    print(f"Created default config at {path}")
    print("Please edit it with your Intempus credentials, then re-run.")


def load_config(path: Path | None = None) -> Config:
    resolved = path or CONFIG_PATH
    if not resolved.exists():
        _create_default_config(resolved)
        sys.exit(0)

    with resolved.open("rb") as f:
        data = tomllib.load(f)

    auth_data = data.get("auth", {})
    missing = [k for k in ("base_url", "username", "password") if not auth_data.get(k)]
    if missing:
        raise ValueError(f"Missing fields in {resolved}: {', '.join(missing)}")

    bonus: BonusConfig | None = None
    if "bonus" in data:
        b = data["bonus"]
        if "hourly_rate" not in b:
            raise ValueError(f"[bonus] section in {resolved} is missing 'hourly_rate'")
        bonus = BonusConfig(
            hourly_rate=float(b["hourly_rate"]),
            projects=list(b.get("projects", [])),
            min_hours=float(b.get("min_hours", 0.0)),
        )

    return Config(
        auth=AuthConfig(
            base_url=auth_data["base_url"].rstrip("/"),
            username=auth_data["username"],
            password=auth_data["password"],
        ),
        bonus=bonus,
    )

