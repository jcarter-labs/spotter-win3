"""Live check: does the server accept the exact string produced by
ClusterProfile.filter_command()? (Constitution rule 3 — verify the real
command, not an approximation of it, before committing Task 2.)
"""

import time

from spotter_win3.cluster import ClusterConnection
from spotter_win3.cluster_profiles import NC7J

HOST, PORT, CALLSIGN = NC7J.hosts[0][0], NC7J.hosts[0][1], "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    cmd = NC7J.filter_command(14.045)
    print(f"\n>>> {cmd}")
    conn.send(cmd)
    time.sleep(2)
    for line in conn.read_lines(timeout=2.0):
        print(line)

    print("\n>>> show/dx/filter")
    conn.send("show/dx/filter")
    time.sleep(2)
    for line in conn.read_lines(timeout=2.0):
        print(line)

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
