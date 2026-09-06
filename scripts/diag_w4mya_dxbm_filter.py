"""Live verification of CC-Cluster's real SET/FILTER DXBM syntax (found in
the CC User Manual, Appendix B/C — not a guess) against W4MYA.
"""

import time

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.w4mya.us"
PORT = 7373
CALLSIGN = "N6YU"

NON_CW_SLOTS = (
    "160-SSB",
    "80-RTTY", "80-SSB",
    "60-SSB",
    "40-RTTY", "40-SSB",
    "30-RTTY",
    "20-RTTY", "20-SSB",
    "17-RTTY", "17-SSB",
    "15-RTTY", "15-SSB",
    "12-RTTY", "12-SSB",
    "10-RTTY", "10-SSB",
)


def run(conn: ClusterConnection, cmd: str, wait: float = 2.0) -> None:
    print(f"\n>>> {cmd}")
    conn.send(cmd)
    time.sleep(wait)
    for line in conn.read_lines(timeout=2.0):
        print(line)


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    run(conn, "SET/FILTER DXBM/OFF")
    run(conn, "SH/FILTER DXBM")

    reject_cmd = "SET/FILTER DXBM/REJECT " + ",".join(NON_CW_SLOTS)
    run(conn, reject_cmd, wait=3.0)
    run(conn, "SH/FILTER DXBM")

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
