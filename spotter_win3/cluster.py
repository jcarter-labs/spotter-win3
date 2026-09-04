"""DX cluster telnet connection, spot-line parsing, and the spot model.

Raw sockets, not telnetlib (removed in Python 3.13). Spot-line format and
the RST-on-logoff behavior below were confirmed live against
dxc.nc7j.com:7373 (AR-Cluster v6) — see scripts/diag_cluster_capture.py.
"""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass

_SPOT_RE = re.compile(
    r"^DX de (?P<spotter>\S+):\s+"
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

    def connect(self, post_login_timeout: float = 2.0) -> str:
        self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)
        banner = self._recv_available(self._timeout)
        self._sock.sendall(f"{self._callsign}\r\n".encode("ascii"))
        # Short idle window, not self._timeout: the login response is short
        # and static, so a long wait here just risks swallowing live spot
        # traffic that arrives right after login into the banner text
        # instead of leaving it for read_lines().
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

    def _recv_available(self, timeout: float) -> bytes:
        assert self._sock is not None
        self._sock.settimeout(timeout)
        chunks = []
        try:
            while True:
                data = self._sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        except socket.timeout:
            pass
        return b"".join(chunks)
