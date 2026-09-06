"""Live diagnostic: connect to WA9PIE-2 (DXSpider) and capture the raw
login exchange. Constitution rule 3 — verify before building a profile
for a new cluster software family (DXSpider, not yet used by NC7J/AR-Cluster).
"""

from spotter_win3.cluster import ClusterConnection

HOST = "dxc.wa9pie.net"
PORT = 8000
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
