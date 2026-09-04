# DX Spotter

A desktop app for CW operators: live spots from a DX cluster (currently
NC7J, AR-Cluster) on a vertical frequency bandmap. POTA integration and the
mirrored two-lane layout are not yet built (see `masterplan-v2.md`).

## Setup (Windows)

```
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```
.venv\Scripts\python.exe -m spotter_win3.main
```

Verified working 2026-09-04: connects to `dxc.nc7j.com:7373` as the
configured operator callsign, applies the CW/band filter for the
configured center frequency, and renders live spots on the scope.

## Test

```
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Configuration

Settings persist to `~/.config/spotter-win3/config.json` (created on first
save; see `spotter_win3/config.py` for defaults). Set your operator
callsign there before running — the default (`N0CALL`) will connect but
isn't a real login.
