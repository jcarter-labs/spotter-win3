"""Re-runnable CPU measurement of the app's hot paths, so a refactor targets
measured numbers rather than guesses. No network: spot lines are synthetic
(same layout as the captured AR-Cluster lines in tests/test_cluster.py).

Measures, per unit of work:
  1. ingest   — parse -> queue -> band/CW/dedup -> store.upsert, per spot
  2. scans    — the O(n) per-tick work in App._poll besides rendering
  3. render   — per frame, in a real Tk window: BandScope.render() (artist
                rebuild), Agg rasterize, and the blit of that buffer into
                the Tk widget (FigureCanvasTkAgg.draw() = rasterize + blit)

then converts each to a CPU% estimate at the app's real rates. Task Manager's
CPU column is a percentage of ALL logical CPUs, so both bases are printed.

Run from the repo root:
    .venv\\Scripts\\python.exe -m scripts.profile_hotpaths
    .venv\\Scripts\\python.exe -m scripts.profile_hotpaths --profile
"""

from __future__ import annotations

import argparse
import cProfile
import math
import os
import pstats
import queue
import random
import statistics
import time
import tkinter as tk

from matplotlib.backends.backend_agg import FigureCanvasAgg

from spotter_win3.bandmap import BandScope
from spotter_win3.cluster import parse_spot_line
from spotter_win3.cluster_profiles import band_for_freq_mhz
from spotter_win3.filters import DedupCache, is_cw_mode
from spotter_win3.main import POLL_INTERVAL_MS
from spotter_win3.scope_utils import FADE_REFRESH_SECONDS, RedrawGate, in_window
from spotter_win3.spot_store import SpotStore

CENTER_KHZ = 14045.0
BANDWIDTH_KHZ = 50.0
WINDOW_MINUTES = 10
SPOT_RATES_PER_S = (10, 100, 300)  # typical regional .. unfiltered firehose
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _call(rng: random.Random) -> str:
    prefix = rng.choice(["K", "W", "N", "AA", "DL", "G", "JA", "EA", "OK"])
    return f"{prefix}{rng.randint(0, 9)}{''.join(rng.choice(LETTERS) for _ in range(rng.randint(1, 3)))}"


def make_spot_lines(n: int, seed: int = 0) -> list[str]:
    """``n`` AR-Cluster-format lines, in-band on 20 m, ~1/4 repeat callsigns
    so the dedup path takes both branches. Deterministic for a given seed."""
    rng = random.Random(seed)
    pool = [_call(rng) for _ in range(max(10, n // 4))]
    lines = []
    for _ in range(n):
        spotter = f"{_call(rng)}-#:"
        freq = round(rng.uniform(14000.0, 14350.0), 1)
        head = f"DX de {spotter:<13}{freq:>8.1f}  {rng.choice(pool):<12} CW {rng.randint(3, 30)} dB {rng.randint(12, 35)} WPM CQ"
        lines.append(f"{head:<70}{rng.randint(0, 23):02d}{rng.randint(0, 59):02d}Z")
    return lines


def populate_store(store: SpotStore, n_cluster: int, n_pota: int, now: float, seed: int = 1) -> None:
    """In-window spots shaped like the real screen: part uniform, part tight
    clusters (which is what triggers declutter + leader lines)."""
    rng = random.Random(seed)
    half = BANDWIDTH_KHZ / 2

    def freq(i: int) -> float:
        if i % 5 < 2:  # 40% in two tight clusters
            return CENTER_KHZ + rng.choice((-2.0, 2.0)) + rng.uniform(-0.15, 0.15)
        return CENTER_KHZ + rng.uniform(-half, half)

    for i in range(n_cluster):
        store.upsert(f"C{i:03d}", "20m", "cluster", freq(i), "SPOTTER", "CW", now=now - rng.uniform(0, 540))
    for i in range(n_pota):
        store.upsert(f"P{i:03d}", "20m", "pota", freq(i), "SPOTTER", "CW", now=now - rng.uniform(0, 540))


def bench_ingest(lines: list[str]) -> float:
    """Seconds per spot through the whole parse -> UI-thread path."""
    q: queue.Queue = queue.Queue()
    dedup, store = DedupCache(), SpotStore()
    t0 = time.perf_counter()
    for line in lines:  # worker thread side
        spot = parse_spot_line(line)
        if spot:
            q.put(("spot", spot))
    while True:  # UI thread side (App._poll / _handle_spot)
        try:
            _, spot = q.get_nowait()
        except queue.Empty:
            break
        band = band_for_freq_mhz(spot.freq_khz / 1000)
        if not is_cw_mode(spot) or dedup.is_duplicate(spot.dx_call, band):
            continue
        store.upsert(spot.dx_call, band, "cluster", spot.freq_khz, spot.spotter, spot.comment)
    return (time.perf_counter() - t0) / len(lines)


def bench_scans(store: SpotStore, reps: int) -> float:
    """Seconds per tick of App._poll's non-render O(n) work."""
    t0 = time.perf_counter()
    for _ in range(reps):
        store.prune(WINDOW_MINUTES * 60)
        store.spots_for_feed("cluster")
        store.spots_for_feed("pota")
        sum(1 for s in store.spots_for_feed("cluster") if in_window(s.freq_khz, CENTER_KHZ, BANDWIDTH_KHZ))
        sum(1 for s in store.spots_for_feed("pota") if in_window(s.freq_khz, CENTER_KHZ, BANDWIDTH_KHZ))
    return (time.perf_counter() - t0) / reps


def bench_render(scope: BandScope, store: SpotStore, reps: int) -> tuple[float, float, float]:
    """(build_s, raster_s, blit_s) medians per frame. FigureCanvasTkAgg.draw()
    is FigureCanvasAgg.draw() then blit(); timed separately here, which is the
    synchronous equivalent of the draw_idle() the app schedules."""
    build, raster, blit = [], [], []
    for _ in range(reps):
        t0 = time.perf_counter()
        scope.render(
            store.spots_for_feed("cluster"), store.spots_for_feed("pota"),
            CENTER_KHZ, BANDWIDTH_KHZ, WINDOW_MINUTES,
        )
        t1 = time.perf_counter()
        FigureCanvasAgg.draw(scope.canvas)
        t2 = time.perf_counter()
        scope.canvas.blit()
        t3 = time.perf_counter()
        build.append(t1 - t0)
        raster.append(t2 - t1)
        blit.append(t3 - t2)
    return statistics.median(build), statistics.median(raster), statistics.median(blit)


def simulate_redraws_per_s(spot_rate: float, hz: float, seconds: float = 120.0, seed: int = 7) -> float:
    """Redraws/s the real RedrawGate allows at ``hz`` ticks/s with Poisson spot
    arrivals (any arrival in a tick marks it dirty). Deterministic per seed."""
    rng = random.Random(seed)
    gate, dt = RedrawGate(), 1.0 / hz
    p_arrival = 1.0 - math.exp(-spot_rate * dt)
    redraws, now = 0, 0.0
    for _ in range(int(seconds * hz)):
        if rng.random() < p_arrival:
            gate.mark_dirty()
        redraws += gate.should_redraw(now)
        now += dt
    return redraws / seconds


def pct(seconds_per_s: float, logical_cpus: int) -> str:
    return f"{seconds_per_s * 100:5.2f}% of a core / {seconds_per_s * 100 / logical_cpus:5.2f}% of total"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--reps", type=int, default=60, help="render frames to time")
    ap.add_argument("--cluster-spots", type=int, default=60)
    ap.add_argument("--pota-spots", type=int, default=15)
    ap.add_argument("--hz", type=float, default=1000 / POLL_INTERVAL_MS, help="UI tick rate")
    ap.add_argument("--profile", action="store_true", help="cProfile render()+draw()")
    args = ap.parse_args()
    cpus = os.cpu_count() or 1

    per_spot = bench_ingest(make_spot_lines(20000))

    root = tk.Tk()
    root.geometry("590x1360+0+0")
    scope = BandScope(root)
    scope.pack(fill=tk.BOTH, expand=True)
    root.update()  # real layout, so winfo_height() is real
    store = SpotStore()
    populate_store(store, args.cluster_spots, args.pota_spots, time.monotonic())

    bench_render(scope, store, 5)  # warm-up: font cache, first layout
    per_scan = bench_scans(store, 2000)
    build_s, raster_s, blit_s = bench_render(scope, store, args.reps)

    print(f"Logical CPUs: {cpus}   tick rate: {args.hz:g} Hz   "
          f"scene: {args.cluster_spots} RBN + {args.pota_spots} POTA spots, {root.winfo_height()} px tall\n")
    print(f"{'stage':<34}{'per unit':>14}   CPU at app rate")
    print("-" * 96)
    for rate in SPOT_RATES_PER_S:
        print(f"{'ingest @ ' + str(rate) + ' spots/s':<34}{per_spot * 1e6:>11.1f} µs   {pct(per_spot * rate, cpus)}")
    print(f"{'per-tick scans':<34}{per_scan * 1e6:>11.1f} µs   {pct(per_scan * args.hz, cpus)}")
    print(f"{'render() artist rebuild':<34}{build_s * 1e3:>11.2f} ms   {pct(build_s * args.hz, cpus)}")
    print(f"{'Agg rasterize':<34}{raster_s * 1e3:>11.2f} ms   {pct(raster_s * args.hz, cpus)}")
    print(f"{'Tk blit (buffer -> widget)':<34}{blit_s * 1e3:>11.2f} ms   {pct(blit_s * args.hz, cpus)}")
    frame_s = build_s + raster_s + blit_s
    total = (frame_s + per_scan) * args.hz
    print("-" * 96)
    print(f"{'UI tick demand (scans+frame)':<34}{frame_s * 1e3:>11.2f} ms   {pct(total, cpus)}")
    print(f"UI thread is one core: demand above 100% of a core saturates at "
          f"{100 / cpus:.2f}% of total.")

    print(f"\nWith RedrawGate (skips unchanged ticks; fade refresh every {FADE_REFRESH_SECONDS:g} s):")
    print(f"{'spot arrivals':<34}{'redraws/s':>14}   CPU (frame cost x redraws/s)")
    for rate in (0, 1, 3, 10):
        rps = simulate_redraws_per_s(rate, args.hz)
        print(f"{str(rate) + ' spots/s':<34}{rps:>14.2f}   {pct((frame_s + per_scan) * rps + per_scan * args.hz, cpus)}")

    if args.profile:
        prof = cProfile.Profile()
        prof.enable()
        bench_render(scope, store, 30)
        prof.disable()
        print("\ncProfile, 30 frames of render()+draw(), top 15 by cumulative time:")
        pstats.Stats(prof).sort_stats("cumulative").print_stats(15)

    root.destroy()


if __name__ == "__main__":
    main()
