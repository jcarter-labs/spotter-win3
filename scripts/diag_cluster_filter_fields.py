"""Live diagnostic: determine whether NC7J's AR-Cluster supports server-side
mode/CW filtering, or whether the spec's client-side fallback is the only
option for this profile (Constitution 7b(a) — verify, don't infer).
"""

import time

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.nc7j.com"
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
    print(conn.connect())

    run(conn, "help dx")
    run(conn, "show/dx/filter")
    run(conn, "set dx filter mode=cw")
    run(conn, "show/dx/filter")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
