"""Live diagnostic: verify the exact DXSpider filter command this profile
will issue (accept/spots on <band>/cw) is accepted by WA9PIE-2, per
Constitution rule 3 — confirm the real command works before committing to
it in cluster_profiles.py.
"""

import time

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.wa9pie.net"
PORT = 8000
CALLSIGN = "N6YU"


def run(conn: ClusterConnection, cmd: str, wait: float = 2.0) -> None:
    print(f"\n>>> {cmd}")
    conn.send(cmd)
    time.sleep(wait)
    for line in conn.read_lines(timeout=2.0):
        print(line)


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect(banner_timeout=5.0, post_login_timeout=3.0))

    run(conn, "clear/spots all")
    run(conn, "accept/spots on 20m/cw")
    run(conn, "show/filter")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
