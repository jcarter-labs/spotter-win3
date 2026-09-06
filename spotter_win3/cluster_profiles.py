"""Per-cluster filter-command dialects (spec item 7). Each profile below
was verified live against its real server before being added — see the
matching scripts/diag_<name>_*.py for the discovery/verification session:

- NC7J (AR-Cluster v6): diag_cluster_filter_fields.py,
  diag_verify_filter_command.py. Single unified mode+band filter.
- WA9PIE-2 (DXSpider): diag_wa9pie_connect.py, diag_wa9pie_filter_fields.py,
  diag_wa9pie_verify_filter.py, diag_wa9pie_verify_rbn_filter.py. DXSpider
  splits manual spots and RBN/skimmer spots into two separate filter
  classes (accept/spots and accept/rbn) — both need setting for full CW
  coverage.
- W3LPL (DXSpider): diag_w3lpl_verify.py. Same software as WA9PIE-2, so
  only the dialect's applicability was re-confirmed, not rediscovered.
- W4MYA (CC-Cluster v3.397): diag_w4mya_connect.py, diag_w4mya_filter_fields.py,
  diag_w4mya_try_commands.py. No working server-side band+mode filter
  command was found — "help filter"/"help set" both error, the only
  online help is an external web page, and three plausible command
  guesses (AR-Cluster-style, and two CC-Cluster-style guesses) all
  errored. Per Constitution rule 10 (stop after two failed attempts, do
  not guess a third — this had three), no further syntax was guessed.
  This profile marks cw_trustworthy=False and relies entirely on the
  client-side is_cw_mode() fallback (spec item 7's designed-for case).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

_BAND_EDGES_MHZ = {
    "160": (1.8, 2.0),
    "80": (3.5, 4.0),
    "60": (5.06, 5.45),
    "40": (7.0, 7.3),
    "30": (10.1, 10.15),
    "20": (14.0, 14.35),
    "17": (18.068, 18.168),
    "15": (21.0, 21.45),
    "12": (24.89, 24.99),
    "10": (28.0, 29.7),
}

_DXSPIDER_BAND_LABELS = {band: f"{band}m" for band in _BAND_EDGES_MHZ}


def band_for_freq_mhz(freq_mhz: float) -> str:
    for band, (low, high) in _BAND_EDGES_MHZ.items():
        if low <= freq_mhz <= high:
            return band
    raise ValueError(f"{freq_mhz} MHz is not within a known HF amateur band")


FilterDialect = Callable[[float], list[str]]


def _ar_cluster_dialect(freq_mhz: float) -> list[str]:
    band = band_for_freq_mhz(freq_mhz)
    return [f"set dx filter mode = cw and band = {band}"]


def _dxspider_dialect(freq_mhz: float) -> list[str]:
    band = band_for_freq_mhz(freq_mhz)
    label = _DXSPIDER_BAND_LABELS[band]
    return [
        f"accept/spots on {label}/cw",
        f"accept/rbn on {label}/cw",
    ]


def _no_verified_dialect(freq_mhz: float) -> list[str]:
    # Still validates the frequency (raises ValueError out-of-band) so
    # every profile behaves consistently for bad input, but issues no
    # server-side command — see the W4MYA note in the module docstring.
    band_for_freq_mhz(freq_mhz)
    return []


@dataclass(frozen=True)
class ClusterProfile:
    name: str
    hosts: tuple[tuple[str, int], ...]
    cw_trustworthy: bool
    _dialect: FilterDialect

    def filter_commands(self, center_freq_mhz: float) -> list[str]:
        """All commands this profile needs sent for a band change. Use
        this, not filter_command(), for anything issuing more than one
        command (e.g. DXSpider's separate spots/rbn filters)."""
        return self._dialect(center_freq_mhz)

    def filter_command(self, center_freq_mhz: float) -> str:
        """Single-command convenience wrapper — preserved for backward
        compatibility with NC7J's original one-command API. Returns the
        first command, or "" if the profile issues none."""
        commands = self.filter_commands(center_freq_mhz)
        return commands[0] if commands else ""


NC7J = ClusterProfile(
    name="NC7J (AR-Cluster)",
    hosts=(("dxc.nc7j.com", 7373),),
    cw_trustworthy=True,
    _dialect=_ar_cluster_dialect,
)

WA9PIE2 = ClusterProfile(
    name="WA9PIE-2 (DXSpider)",
    hosts=(("dxc.wa9pie.net", 8000),),
    cw_trustworthy=True,
    _dialect=_dxspider_dialect,
)

W3LPL = ClusterProfile(
    name="W3LPL (DXSpider)",
    hosts=(("w3lpl.net", 7373),),
    cw_trustworthy=True,
    _dialect=_dxspider_dialect,
)

W4MYA = ClusterProfile(
    name="W4MYA (CC-Cluster)",
    hosts=(("dxc.w4mya.us", 7373),),
    cw_trustworthy=False,
    _dialect=_no_verified_dialect,
)

PROFILES: dict[str, ClusterProfile] = {
    p.name: p for p in (NC7J, WA9PIE2, W3LPL, W4MYA)
}
DEFAULT_PROFILE = NC7J
