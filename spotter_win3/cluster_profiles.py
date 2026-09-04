"""Per-cluster filter-command dialects. Only NC7J (AR-Cluster) is wired —
the server/profile picker and its persistence are deferred by decision
(masterplan spec item 7).

Server-side ``mode = cw`` filtering was confirmed live against
dxc.nc7j.com:7373 via scripts/diag_cluster_filter_fields.py (the server
accepted it and began streaming CW-only spots), so this profile marks
CW filtering as trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass

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


def band_for_freq_mhz(freq_mhz: float) -> str:
    for band, (low, high) in _BAND_EDGES_MHZ.items():
        if low <= freq_mhz <= high:
            return band
    raise ValueError(f"{freq_mhz} MHz is not within a known HF amateur band")


@dataclass(frozen=True)
class ClusterProfile:
    name: str
    hosts: tuple[tuple[str, int], ...]
    cw_trustworthy: bool

    def filter_command(self, center_freq_mhz: float) -> str:
        band = band_for_freq_mhz(center_freq_mhz)
        return f"set dx filter mode = cw and band = {band}"


NC7J = ClusterProfile(
    name="NC7J (AR-Cluster)",
    hosts=(("dxc.nc7j.com", 7373),),
    cw_trustworthy=True,
)
