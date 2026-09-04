"""Persistent app configuration — ``~/.config/spotter-win3/config.json`` on
every platform, deliberately uniform rather than OS-idiomatic (spec item 9).
Operator callsign, spotter lists, filtered bands, and host list are
configuration inputs, not source constants (spec item 7).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "spotter-win3"
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class Config:
    operator_callsign: str = ""
    center_freq_mhz: float = 14.045
    bandwidth_khz: int = 50
    window_minutes: int = 10
    spotter_tier: str = "regional"  # "local" | "regional"
    cluster_profile: str = "NC7J (AR-Cluster)"
    spotter_lists: dict[str, list[str]] = field(
        default_factory=lambda: {"local": [], "regional": []}
    )


def load(path: Path = CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Config(**{**asdict(Config()), **data})


def save(config: Config, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
    tmp_path.replace(path)
