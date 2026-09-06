"""DX cluster telnet connection, spot-line parsing, and the spot model.

Raw sockets, not telnetlib (removed in Python 3.13). Spot-line format and
the RST-on-logoff behavior below were confirmed live against
dxc.nc7j.com:7373 (AR-Cluster v6) — see scripts/diag_cluster_capture.py.
"""

from __future__ import annotations

import re
import socket
import time
from dataclasses import dataclass

_SPOT_RE = re.compile(
    # Colon-to-frequency gap is normally padded with spaces for column
    # alignment, but a long spotter callsign (e.g. "DL8LAS-3-#") can fill
    # that padding entirely, leaving zero separator — confirmed live via
    # scripts/diag_verify_w4mya_live_spots.py. \s* not \s+.
    r"^DX de (?P<spotter>\S+):\s*"
    r"(?P<freq_khz>\d+(?:\.\d+)?)\s+"
    r"(?P<dx_call>\S+)\s+"
    r"(?P<comment>.*?)\s*"
    r"(?P<time_z>\d{4})Z\s*$"
)


@dataclass(frozen=True)
class Spot:
    spotter: str
    dx_call: str
    freq_khz: float
    comment: str
    time_z: str
    raw: str


def parse_spot_line(line: str) -> Spot | None:
    match = _SPOT_RE.match(line.strip())
    if not match:
        return None
    return Spot(
        spotter=match["spotter"],
        dx_call=match["dx_call"],
        freq_khz=float(match["freq_khz"]),
        comment=match["comment"].strip(),
        time_z=match["time_z"],
        raw=line,
    )


class ClusterConnection:
    """A single telnet session to a DX cluster (AR-Cluster dialect)."""

    def __init__(self, host: str, port: int, callsign: str, timeout: float = 10.0):
        self._host = host
        self._port = port
        self._callsign = callsign
        self._timeout = timeout
        self._sock: socket.socket | None = None
        self._buf = b""

    def connect(self, banner_timeout: float = 3.0, post_login_timeout: float = 2.0) -> str:
        self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)
        banner = self._recv_available(banner_timeout)
        self._sock.sendall(f"{self._callsign}\r\n".encode("ascii"))
        banner += self._recv_available(post_login_timeout)
        return banner.decode("ascii", errors="replace")

    def send(self, command: str) -> None:
        assert self._sock is not None
        self._sock.sendall(f"{command}\r\n".encode("ascii"))

    def read_lines(self, timeout: float = 1.0):
        assert self._sock is not None
        self._sock.settimeout(timeout)
        try:
            data = self._sock.recv(4096)
            if data:
                self._buf += data
        except socket.timeout:
            pass
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            yield line.decode("ascii", errors="replace").rstrip("\r")

    def close(self) -> None:
        if self._sock is None:
            return
        try:
            self.send("bye")
            self._recv_available(2.0)
        except OSError:
            pass  # server RSTs on logoff — confirmed AR-Cluster v6 behavior
        finally:
            self._sock.close()
            self._sock = None

    def _recv_available(self, total_timeout: float) -> bytes:
        """Reads for up to total_timeout seconds and returns whatever
        arrived. Bounded by total elapsed time, not by an idle gap — a
        server that streams continuously (e.g. this login's persisted
        live-spot filter) never produces an idle gap, so an idle-gap-based
        read would never return.
        """
        assert self._sock is not None
        deadline = time.monotonic() + total_timeout
        chunks = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self._sock.settimeout(min(remaining, 0.5))
            try:
                data = self._sock.recv(4096)
            except socket.timeout:
                continue
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks)
