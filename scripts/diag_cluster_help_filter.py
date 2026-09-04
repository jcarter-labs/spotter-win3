"""Live diagnostic: query the cluster's own help text for DX filter syntax,
so the Mode/CW filter command is based on real documentation, not a guess
extrapolated from the two examples in the login banner (Constitution 7b(a)).
"""

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.nc7j.com"
PORT = 7373
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    for cmd in ("help filter", "help set/filter", "help set dx filter"):
        print(f"\n>>> {cmd}")
        conn.send(cmd)
        import time

        time.sleep(2)
        for line in conn.read_lines(timeout=2.0):
            print(line)

    conn.close()
    print("\nClosed.")


if __name__ == "__main__":
    main()
