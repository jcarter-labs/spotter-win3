"""Live smoke test for the production ClusterConnection class (not the raw
throwaway diagnostics) — Constitution rule 3, confirming the built class
works before Task 1 is committed.
"""

import time

from spotter_win3.cluster import ClusterConnection, parse_spot_line

HOST = "dxc.nc7j.com"
PORT = 7373
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print("Connecting via ClusterConnection...")
    banner = conn.connect()
    print("--- BANNER/LOGIN ---")
    print(banner)
    print("--- END ---\n")

    print("Reading lines for ~15s...")
    deadline = time.monotonic() + 15
    seen_spot = False
    while time.monotonic() < deadline:
        for line in conn.read_lines(timeout=1.0):
            spot = parse_spot_line(line)
            if spot:
                seen_spot = True
                print(f"PARSED: {spot}")
            else:
                print(f"RAW:    {line!r}")

    print(f"\nAt least one real spot parsed via the class: {seen_spot}")
    conn.close()
    print("Closed cleanly.")


if __name__ == "__main__":
    main()
