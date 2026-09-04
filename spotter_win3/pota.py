"""POTA (Parks on the Air) activator spot client: public API, no auth,
own polling thread/queue (spec item 8). CW-only via client-side filtering
on the API's own "mode" field — endpoint and response shape confirmed
live via scripts/diag_pota_api.py.

Known limitation (spec/Tech item 5): poll age reflects the last attempt,
not the last success — a failing feed still reports a healthy-looking
age, and request errors are swallowed silently.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass

import requests

POTA_SPOT_URL = "https://api.pota.app/spot/activator"
POLL_INTERVAL_SECONDS = 60.0
REQUEST_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class PotaSpot:
    dx_call: str
    freq_khz: float
    reference: str
    spotter: str
    comment: str
    spot_time: str


def parse_pota_record(record: dict) -> PotaSpot | None:
    if record.get("mode") != "CW":
        return None
    try:
        return PotaSpot(
            dx_call=record["activator"],
            freq_khz=float(record["frequency"]),
            reference=record["reference"],
            spotter=record.get("spotter") or "",
            comment=record.get("comments") or "",
            spot_time=record.get("spotTime", ""),
        )
    except (KeyError, TypeError, ValueError):
        return None


class PotaWorker:
    """Owns the HTTP polling entirely on its own daemon thread. The UI
    thread only ever reads self.incoming."""

    def __init__(
        self,
        poll_interval: float = POLL_INTERVAL_SECONDS,
        url: str = POTA_SPOT_URL,
    ) -> None:
        self._poll_interval = poll_interval
        self._url = url
        self.incoming: queue.Queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.incoming.put(("poll_attempt", time.monotonic()))
            try:
                resp = requests.get(self._url, timeout=REQUEST_TIMEOUT_SECONDS)
                resp.raise_for_status()
                for record in resp.json():
                    spot = parse_pota_record(record)
                    if spot:
                        self.incoming.put(("spot", spot))
            except (requests.RequestException, ValueError):
                pass  # swallowed by design — poll age is attempt-based (spec item 8 / Tech item 5)
            self._stop.wait(self._poll_interval)
