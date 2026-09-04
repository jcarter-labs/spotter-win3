"""Standalone diagnostic: connect to the DX cluster and capture the raw
login exchange. Not part of the app — Constitution rule 3 requires this
verified live before any cluster UI/parser code is written.

Uses raw sockets, not telnetlib (removed in Python 3.13).
"""

import socket
import sys

HOST = "dxc.nc7j.com"
PORT = 7373
CALLSIGN = "N6YU"
TIMEOUT = 10


def recv_available(sock: socket.socket, timeout: float = TIMEOUT) -> bytes:
    sock.settimeout(timeout)
    chunks = []
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    except socket.timeout:
        pass
    return b"".join(chunks)


def main() -> None:
    print(f"Connecting to {HOST}:{PORT} ...")
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
            print("Connected. Reading banner/login prompt...")
            banner = recv_available(sock)
            print("--- RAW BANNER ---")
            print(banner.decode("ascii", errors="replace"))
            print("--- END BANNER ---\n")

            print(f"Sending callsign: {CALLSIGN}")
            sock.sendall(f"{CALLSIGN}\r\n".encode("ascii"))

            response = recv_available(sock)
            print("--- RAW LOGIN RESPONSE ---")
            print(response.decode("ascii", errors="replace"))
            print("--- END LOGIN RESPONSE ---\n")

            print("Sending 'bye' to log off cleanly...")
            sock.sendall(b"bye\r\n")
            farewell = recv_available(sock, timeout=3)
            print("--- RAW FAREWELL ---")
            print(farewell.decode("ascii", errors="replace"))
            print("--- END FAREWELL ---")
    except (TimeoutError, ConnectionRefusedError, OSError) as exc:
        print(f"CONNECTION FAILED: {exc!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
