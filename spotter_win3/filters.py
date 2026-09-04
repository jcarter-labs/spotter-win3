"""Client-side spot filtering: dedup, spotter-tier matching, and the CW
mode-check fallback for profiles that don't mark server-side filtering as
trustworthy (masterplan spec item 7).
"""

from __future__ import annotations

import time

from spotter_win3.cluster import Spot

DEDUP_WINDOW_SECONDS = 120.0


class DedupCache:
    """Suppresses the same call+band within a 2-minute window. Cluster spots
    only — POTA spots are never deduped (spec item 8)."""

    def __init__(self, window_seconds: float = DEDUP_WINDOW_SECONDS):
        self._window = window_seconds
        self._seen: dict[tuple[str, str], float] = {}

    def is_duplicate(self, dx_call: str, band: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        key = (dx_call, band)
        last = self._seen.get(key)
        self._seen[key] = now
        return last is not None and (now - last) < self._window


def matches_spotter_tier(spotter: str, tier_members: set[str]) -> bool:
    """``tier_members`` holds the vetted spotter callsigns for a tier
    (case-insensitive; -# skimmer-node suffixes are their own entries)."""
    return spotter.upper() in {s.upper() for s in tier_members}


def is_cw_mode(spot: Spot) -> bool:
    """Client-side authoritative fallback for profiles that don't mark
    server-side CW filtering as trustworthy (spec item 7)."""
    return "CW" in spot.comment.upper().split()
