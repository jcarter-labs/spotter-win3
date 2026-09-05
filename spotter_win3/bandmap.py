"""Bandmap scope widget: vertical frequency spine, RBN and POTA spots each
in their own lane (left/right), plotted by frequency with alpha-fade
aging. No boxed border — left spine + tick labels only, transparent
background (spec item 4). The POTA lane gets a mirrored spine + tick
marks (no duplicate numeric labels, since both lanes share one frequency
range) drawn manually rather than via a second Axes, and each lane runs
its own greedy declutter pass so close-frequency labels don't overlap —
matching the reference screenshot's staggered-label behavior.
"""

from __future__ import annotations

import time
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from spotter_win3.scope_utils import age_alpha, in_window, y_for_freq

MIN_LABEL_SPACING = 0.03  # fraction of axes height between adjacent labels
TICK_HALF_WIDTH = 0.02


class BandScope(tk.Frame):
    def __init__(self, master: tk.Widget, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.figure = Figure(figsize=(3, 8), dpi=100)
        self.figure.patch.set_alpha(0.0)
        self.ax = self.figure.add_subplot(111)
        self.ax.patch.set_alpha(0.0)
        for side in ("top", "right", "bottom"):
            self.ax.spines[side].set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0, 1)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self._on_click)

        self._artists: list = []
        self._spot_positions: list[tuple[float, str]] = []

    def render(
        self,
        cluster_spots,
        pota_spots,
        center_khz: float,
        bandwidth_khz: float,
        window_minutes: float,
        now: float | None = None,
    ) -> None:
        now = time.monotonic() if now is None else now
        window_seconds = window_minutes * 60

        for artist in self._artists:
            artist.remove()
        self._artists.clear()
        self._spot_positions.clear()

        half = bandwidth_khz / 2
        low, high = center_khz - half, center_khz + half
        ticks = [low, center_khz, high]
        tick_ys = [y_for_freq(t, center_khz, bandwidth_khz) for t in ticks]
        self.ax.set_yticks(tick_ys)
        self.ax.set_yticklabels([f"{t / 1000:.3f}" for t in ticks])

        # Mirrored spine on the POTA side: a plain vertical line + tick
        # dashes, no numeric labels (both lanes share one frequency axis).
        (mirror_spine,) = self.ax.plot([1.0, 1.0], [0, 1], color="black", linewidth=0.8)
        self._artists.append(mirror_spine)
        for ty in tick_ys:
            (tick,) = self.ax.plot(
                [1.0 - TICK_HALF_WIDTH, 1.0], [ty, ty], color="black", linewidth=0.8
            )
            self._artists.append(tick)

        self._render_lane(
            cluster_spots, center_khz, bandwidth_khz, window_seconds, now,
            x=0.08, ha="left", color="navy", label_dir=1,
        )
        self._render_lane(
            pota_spots, center_khz, bandwidth_khz, window_seconds, now,
            x=0.92, ha="right", color="darkgreen", label_dir=-1,
        )

        self.canvas.draw_idle()

    def _render_lane(
        self, spots, center_khz, bandwidth_khz, window_seconds, now, *, x, ha, color, label_dir
    ) -> None:
        visible = [s for s in spots if in_window(s.freq_khz, center_khz, bandwidth_khz)]
        visible.sort(key=lambda s: s.freq_khz)
        if not visible:
            return

        true_ys = [y_for_freq(s.freq_khz, center_khz, bandwidth_khz) for s in visible]
        display_ys = _declutter(true_ys)

        for spot, true_y, display_y in zip(visible, true_ys, display_ys):
            age = now - spot.last_seen
            alpha = age_alpha(age, window_seconds)
            text = self.ax.text(
                x, display_y, spot.dx_call,
                va="center", ha=ha, alpha=alpha, fontsize=8, color=color,
            )
            self._artists.append(text)
            self._spot_positions.append((display_y, spot.dx_call))

            if abs(display_y - true_y) > 1e-6:
                connector_x = x - 0.03 * label_dir
                (line,) = self.ax.plot(
                    [connector_x, connector_x - 0.02 * label_dir],
                    [true_y, display_y],
                    color=color, linewidth=0.5, alpha=alpha * 0.6,
                )
                self._artists.append(line)

    def _on_click(self, event) -> None:
        if event.ydata is None or not self._spot_positions:
            return
        _, call = min(self._spot_positions, key=lambda p: abs(p[0] - event.ydata))
        try:
            self.clipboard_clear()
            self.clipboard_append(call)
        except tk.TclError:
            pass


def _declutter(true_ys: list[float]) -> list[float]:
    """Greedy minimum-spacing enforcement on a list already sorted
    ascending: pushes a label up just enough to clear the previous one."""
    if not true_ys:
        return []
    adjusted = [true_ys[0]]
    for y in true_ys[1:]:
        prev = adjusted[-1]
        adjusted.append(y if y - prev >= MIN_LABEL_SPACING else prev + MIN_LABEL_SPACING)
    return adjusted
