"""In-memory spot store keyed by (call, band, feed) so cluster and POTA
spots never evict each other (Tech item 2).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class StoredSpot:
    dx_call: str
    band: str
    feed: str  # "cluster" | "pota"
    freq_khz: float
    spotter: str
    comment: str
    first_seen: float
    last_seen: float


class SpotStore:
    def __init__(self) -> None:
        self._spots: dict[tuple[str, str, str], StoredSpot] = {}

    def upsert(
        self,
        dx_call: str,
        band: str,
        feed: str,
        freq_khz: float,
        spotter: str,
        comment: str,
        now: float | None = None,
    ) -> None:
        now = time.monotonic() if now is None else now
        key = (dx_call, band, feed)
        existing = self._spots.get(key)
        if existing:
            existing.freq_khz = freq_khz
            existing.spotter = spotter
            existing.comment = comment
            existing.last_seen = now
        else:
            self._spots[key] = StoredSpot(
                dx_call=dx_call,
                band=band,
                feed=feed,
                freq_khz=freq_khz,
                spotter=spotter,
                comment=comment,
                first_seen=now,
                last_seen=now,
            )

    def prune(self, horizon_seconds: float, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        cutoff = now - horizon_seconds
        for key in [k for k, s in self._spots.items() if s.last_seen < cutoff]:
            del self._spots[key]

    def spots_for_feed(self, feed: str) -> list[StoredSpot]:
        return [s for s in self._spots.values() if s.feed == feed]

    def __len__(self) -> int:
        return len(self._spots)
