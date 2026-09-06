"""Live diagnostic: connect to W4MYA (CC-Cluster v3.397) and capture the
raw login exchange. Third distinct cluster software family in this build —
full discovery needed, same as NC7J originally (Constitution rule 3).
"""

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.w4mya.us"
PORT = 7373
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(f"Connecting to {HOST}:{PORT} ...")
    banner = conn.connect(banner_timeout=5.0, post_login_timeout=3.0)
    print("--- BANNER/LOGIN ---")
    print(banner)
    print("--- END ---")
    conn.close()
    print("Closed.")


if __name__ == "__main__":
    main()
