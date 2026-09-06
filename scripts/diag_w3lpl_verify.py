"""Live diagnostic: W3LPL runs DXSpider too (same family as WA9PIE-2) —
lighter confirmation pass rather than full rediscovery: connect, login,
and confirm the same accept/spots + accept/rbn dialect is accepted here.
"""

import time

from spotter_win3.cluster import ClusterConnection

HOST = "w3lpl.net"
PORT = 7373
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
    run(conn, "clear/rbn all")
    run(conn, "accept/rbn on 20m/cw")
    run(conn, "show/filter")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
