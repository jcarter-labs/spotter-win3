"""Raw-line visibility into W3LPL after setting the filter — the worker-
level test showed status=True but zero parsed spots in 20s. Need to see
what's actually arriving (nothing at all? unparseable lines? an error
response to the filter command itself?).
"""

from spotter_win3.cluster import ClusterConnection
from spotter_win3.cluster_profiles import W3LPL

HOST, PORT = W3LPL.hosts[0]
CALLSIGN = "N6YU"


def main() -> None:
    conn = ClusterConnection(HOST, PORT, CALLSIGN)
    print(conn.connect())

    commands = W3LPL.filter_commands(7.050)
    print(f"\nSending commands: {commands}")
    for cmd in commands:
        print(f">>> {cmd}")
        conn.send(cmd)
        import time

        time.sleep(2)
        for line in conn.read_lines(timeout=2.0):
            print(f"RAW: {line!r}")

    print("\n--- Listening for 20s ---")
    import time

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        for line in conn.read_lines(timeout=1.0):
            print(f"RAW: {line!r}")

    conn.close()
    print("Closed.")


if __name__ == "__main__":
    main()
