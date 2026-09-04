"""Standalone diagnostic: capture real spot traffic from the DX cluster for
~30s after login, to base the spot-line parser on actual data rather than a
remembered/assumed format (Constitution rule 3 / 7b(a)).

Uses raw sockets, not telnetlib (removed in Python 3.13).
"""

import socket
import sys
import time

HOST = "dxc.nc7j.com"
PORT = 7373
CALLSIGN = "N6YU"
CONNECT_TIMEOUT = 10
CAPTURE_SECONDS = 30


def recv_available(sock: socket.socket, timeout: float) -> bytes:
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
        with socket.create_connection((HOST, PORT), timeout=CONNECT_TIMEOUT) as sock:
            banner = recv_available(sock, CONNECT_TIMEOUT)
            print(banner.decode("ascii", errors="replace"))

            sock.sendall(f"{CALLSIGN}\r\n".encode("ascii"))
            login_response = recv_available(sock, CONNECT_TIMEOUT)
            print(login_response.decode("ascii", errors="replace"))

            print(f"--- CAPTURING for {CAPTURE_SECONDS}s ---")
            sock.settimeout(1.0)
            buf = b""
            deadline = time.monotonic() + CAPTURE_SECONDS
            while time.monotonic() < deadline:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        ts = time.strftime("%H:%M:%S")
                        text = line.decode("ascii", errors="replace").rstrip("\r")
                        print(f"[{ts}] {text!r}")
                except socket.timeout:
                    continue
            print("--- CAPTURE END ---")

            try:
                sock.sendall(b"bye\r\n")
                recv_available(sock, 3)
            except OSError:
                pass  # server RSTs on logoff — expected, see diag_cluster_connect.py
    except (TimeoutError, ConnectionRefusedError, OSError) as exc:
        print(f"CONNECTION FAILED: {exc!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
