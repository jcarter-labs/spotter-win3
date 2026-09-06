"""Live diagnostic: W4MYA's help system only points to an external web
page and "help filter"/"help set" both error, so probe candidate filter
commands directly and read the server's own response/error text — this
is CC-Cluster v3.397, a third distinct software family, nothing assumed
from AR-Cluster or DXSpider (Constitution rule 3 / 7b(a)).
"""

import time

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.w4mya.us"
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

    # AR-Cluster-style (some CC-Cluster builds emulate this for interop)
    run(conn, "set dx filter mode = cw and band = 20")
    run(conn, "show/filter")

    # CC-Cluster's own apparent bandmode-filter vocabulary, guessed from
    # the show/filter output format itself ("BandMode Filter... Reject:
    # 2-CW,1-CW,...") — testing, not assuming, and reading the error text.
    run(conn, "set/bandmode accept 20-cw")
    run(conn, "set/dxfilter mode cw band 20")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
