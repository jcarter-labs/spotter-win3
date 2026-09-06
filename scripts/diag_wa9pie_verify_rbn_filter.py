"""Live diagnostic: DXSpider separates 'spots' (manual) and 'rbn' (skimmer)
filter classes — confirmed via scripts/diag_wa9pie_verify_filter.py, which
left the account's old pre-existing 'rbn' filter (by-spotter list from a
prior session) untouched. Verify accept/rbn takes the same on/<band>/cw
syntax before the profile relies on it for full CW coverage.
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

    run(conn, "clear/rbn all")
    run(conn, "accept/rbn on 20m/cw")
    run(conn, "show/filter")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
