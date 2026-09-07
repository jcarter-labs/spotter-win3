"""Test the actual ClusterWorker class against W4MYA — the raw-telnet
diagnostic proved the server/filter delivers real CW spots, so if this
also shows zero, the bug is in ClusterWorker/main.py, not the cluster
connection itself."""

import time

from spotter_win3.cluster_profiles import W4MYA
from spotter_win3.main import ClusterWorker

worker = ClusterWorker(W4MYA, "N0CALL")
start = time.monotonic()
print(f"[{0.0:.1f}s] starting worker against {W4MYA.hosts}...")
worker.start()
worker.set_filter_commands(W4MYA.filter_commands(14.045))

deadline = start + 45
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
            if spot_count <= 5:
                print(f"[{time.monotonic() - start:.1f}s] spot: {payload}")
    except Exception:
        pass

print(f"\n[{time.monotonic() - start:.1f}s] done. status={saw_status} spot_count={spot_count}")
worker.stop()
