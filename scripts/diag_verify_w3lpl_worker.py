"""Isolated live test of ClusterWorker against W3LPL specifically — the
operator caught the app showing red/disconnected with W3LPL selected,
and it hadn't actually been confirmed to deliver spots end-to-end
through the real worker (only a lighter filter-acceptance check was
done). Same approach as diag_worker_isolated.py (which caught the
connect() hang bug for NC7J).
"""

import time

from spotter_win3.cluster_profiles import W3LPL
from spotter_win3.main import ClusterWorker

worker = ClusterWorker(W3LPL, "N6YU")
start = time.monotonic()
print(f"[{0.0:.1f}s] starting worker against {W3LPL.hosts}...")
worker.start()
worker.set_filter_commands(W3LPL.filter_commands(14.045))

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
            if spot_count <= 5:
                print(f"[{time.monotonic() - start:.1f}s] spot: {payload}")
    except Exception:
        pass

print(f"\n[{time.monotonic() - start:.1f}s] done. status={saw_status} spot_count={spot_count}")
worker.stop()
