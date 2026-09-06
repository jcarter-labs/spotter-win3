"""Direct proof, right now, that W4MYA (CC-Cluster) actually delivers CW
spots through the real filter command — operator caught zero RBN spots
after 5 minutes in the running app and asked for proof, not a re-cited
claim. Connects, sends the exact W4MYA.filter_commands() output, and
listens long enough (60s) to be conclusive either way.
"""

import time

from spotter_win3.cluster import ClusterConnection, parse_spot_line
from spotter_win3.cluster_profiles import W4MYA

HOST, PORT = W4MYA.hosts[0]
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    commands = W4MYA.filter_commands(14.045)
    print(f"\nSending commands: {commands}")
    for cmd in commands:
        print(f">>> {cmd}")
        conn.send(cmd)
        time.sleep(2)
        for line in conn.read_lines(timeout=2.0):
            print(f"RAW: {line!r}")

    print("\n--- Listening for 60s ---")
    deadline = time.monotonic() + 60
    total_lines = 0
    spot_count = 0
    non_cw_count = 0
    while time.monotonic() < deadline:
        for line in conn.read_lines(timeout=1.0):
            total_lines += 1
            print(f"[{time.monotonic() - deadline + 60:.1f}s] RAW: {line!r}")
            spot = parse_spot_line(line)
            if spot:
                spot_count += 1
                if "CW" not in spot.comment.upper():
                    non_cw_count += 1
                    print(f"  ^^ NON-CW SPOT: comment={spot.comment!r}")

    print(f"\nTotal lines: {total_lines}, parsed spots: {spot_count}, non-CW among them: {non_cw_count}")
    conn.close()
    print("Closed.")


if __name__ == "__main__":
    main()
