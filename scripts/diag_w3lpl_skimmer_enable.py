"""Verify the diagnosis: W3LPL needs an explicit skimmer-enable command
(banner: "CW skimmer spots are defaulted OFF") in addition to the
accept/rbn filter — accept/rbn alone got accepted but delivered zero
spots in a 20s listen (diag_w3lpl_raw_lines.py).
"""

import time

from spotter_win3.cluster import ClusterConnection
from spotter_win3.cluster_profiles import W3LPL

HOST, PORT = W3LPL.hosts[0]
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    for cmd in ["set/skimmer cw"] + W3LPL.filter_commands(14.045):
        print(f"\n>>> {cmd}")
        conn.send(cmd)
        time.sleep(2)
        for line in conn.read_lines(timeout=2.0):
            print(f"RAW: {line!r}")

    print("\n--- Listening for 20s ---")
    deadline = time.monotonic() + 20
    count = 0
    while time.monotonic() < deadline:
        for line in conn.read_lines(timeout=1.0):
            print(f"RAW: {line!r}")
            count += 1

    print(f"\nLines received while listening: {count}")
    conn.close()
    print("Closed.")


if __name__ == "__main__":
    main()
