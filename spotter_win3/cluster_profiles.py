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
- W4MYA (CC-Cluster v3.397): an initial pass (diag_w4mya_connect.py,
  diag_w4mya_filter_fields.py, diag_w4mya_try_commands.py) found "help
  filter"/"help set" both error and three guessed command syntaxes all
  failed, and correctly stopped per Constitution rule 10 rather than
  guess a fourth time. CC-Cluster's real syntax turned out to be
  documented, just not discoverable via in-band help: the CC User
  Manual (VE7CC's own client software, https://www.g4ifb.com/
  CC_User_Manual.pdf, Appendix B/C) documents `SET/FILTER DXBM/REJECT
  <slot,...>`, where each slot names a band+mode segment (e.g.
  "20-RTTY", "40-SSB") rather than mode alone — there is no bare
  "mode=CW" command. Verified live (diag_w4mya_dxbm_filter.py):
  rejecting every non-CW slot across all HF bands leaves only CW spots
  flowing, confirmed by observing real post-filter traffic.
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


# CC-Cluster's DXBM filter has no bare "mode = CW" command — it only
# understands band+mode segments ("20-RTTY", "40-SSB", etc, per the CC
# User Manual Appendix C). CW-only is achieved by rejecting every other
# segment across all recognized HF bands; this list doesn't depend on
# the current band, so the same command is returned regardless of
# freq_mhz (still validated for consistency with the other dialects).
_CC_CLUSTER_NON_CW_SLOTS = (
    "160-SSB",
    "80-RTTY", "80-SSB",
    "60-SSB",
    "40-RTTY", "40-SSB",
    "30-RTTY",
    "20-RTTY", "20-SSB",
    "17-RTTY", "17-SSB",
    "15-RTTY", "15-SSB",
    "12-RTTY", "12-SSB",
    "10-RTTY", "10-SSB",
)


def _cc_cluster_dialect(freq_mhz: float) -> list[str]:
    band_for_freq_mhz(freq_mhz)  # raises ValueError out-of-band, for consistency
    return ["SET/FILTER DXBM/REJECT " + ",".join(_CC_CLUSTER_NON_CW_SLOTS)]


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
    cw_trustworthy=True,
    _dialect=_cc_cluster_dialect,
)

PROFILES: dict[str, ClusterProfile] = {
    p.name: p for p in (NC7J, WA9PIE2, W3LPL, W4MYA)
}
DEFAULT_PROFILE = NC7J
