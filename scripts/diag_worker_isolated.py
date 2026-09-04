"""Isolated live test of ClusterWorker (no Tk) to find where the status
message stalls — the screenshot harness saw "disconnected" even after 15s,
which exceeds connect()'s own worst-case timeout budget (~12s).
"""

import time

from spotter_win3.cluster_profiles import NC7J
from spotter_win3.main import ClusterWorker

worker = ClusterWorker(NC7J, "N6YU")
start = time.monotonic()
print(f"[{0.0:.1f}s] starting worker...")
worker.start()
worker.send_command(NC7J.filter_command(14.045))

deadline = start + 15
while time.monotonic() < deadline:
    try:
        kind, payload = worker.incoming.get(timeout=0.5)
        print(f"[{time.monotonic() - start:.1f}s] {kind}: {payload}")
    except Exception:
        pass

print(f"[{time.monotonic() - start:.1f}s] done, stopping")
worker.stop()
