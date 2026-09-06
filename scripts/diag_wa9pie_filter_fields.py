"""Live diagnostic: discover WA9PIE-2's (DXSpider) real filter-command
syntax via its own help text, rather than assuming it matches AR-Cluster's
dialect. Constitution rule 3 / 7b(a).
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

    run(conn, "help filter")
    run(conn, "help accept")
    run(conn, "help accept/spot")
    run(conn, "show/filter")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
