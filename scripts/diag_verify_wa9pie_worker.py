"""Confirm WA9PIE-2 still works correctly after adding set/skimmer cw to
the shared DXSpider dialect (it previously worked with just the accept/
filters, since it apparently already defaulted skimmer on)."""

import time

from spotter_win3.cluster_profiles import WA9PIE2
from spotter_win3.main import ClusterWorker

worker = ClusterWorker(WA9PIE2, "N6YU")
start = time.monotonic()
print(f"[{0.0:.1f}s] starting worker against {WA9PIE2.hosts}...")
worker.start()
worker.set_filter_commands(WA9PIE2.filter_commands(14.045))

deadline = start + 20
saw_status = None
spot_count = 0
while time.monotonic() < deadline:
    try:
        kind, payload = worker.incoming.get(timeout=0.5)
        if kind == "status":
            saw_status = payload
            print(f"[{time.monotonic() - start:.1f}s] status: {payload}")
        elif kind == "spot":
            spot_count += 1
            if spot_count <= 3:
                print(f"[{time.monotonic() - start:.1f}s] spot: {payload}")
    except Exception:
        pass

print(f"\n[{time.monotonic() - start:.1f}s] done. status={saw_status} spot_count={spot_count}")
worker.stop()
