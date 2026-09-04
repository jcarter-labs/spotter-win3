"""Bandmap scope widget: vertical frequency spine, RBN and POTA spots each
in their own lane (left/right), plotted by frequency with alpha-fade
aging. No boxed border — left spine + tick labels only, transparent
background (spec item 4). Exact mirrored-spine/header styling is the
Task 5 UI polish pass; this lays out functionally distinct lanes only.
"""

from __future__ import annotations

import time
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from spotter_win3.scope_utils import age_alpha, in_window, y_for_freq


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

        self._texts: list = []
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

        for text in self._texts:
            text.remove()
        self._texts.clear()
        self._spot_positions.clear()

        half = bandwidth_khz / 2
        low, high = center_khz - half, center_khz + half
        ticks = [low, center_khz, high]
        self.ax.set_yticks([y_for_freq(t, center_khz, bandwidth_khz) for t in ticks])
        self.ax.set_yticklabels([f"{t / 1000:.3f}" for t in ticks])

        self._render_lane(
            cluster_spots, center_khz, bandwidth_khz, window_seconds, now,
            x=0.08, ha="left", color="navy",
        )
        self._render_lane(
            pota_spots, center_khz, bandwidth_khz, window_seconds, now,
            x=0.92, ha="right", color="darkgreen",
        )

        self.canvas.draw_idle()

    def _render_lane(
        self, spots, center_khz, bandwidth_khz, window_seconds, now, *, x, ha, color
    ) -> None:
        visible = [s for s in spots if in_window(s.freq_khz, center_khz, bandwidth_khz)]
        visible.sort(key=lambda s: s.freq_khz)
        for spot in visible:
            y = y_for_freq(spot.freq_khz, center_khz, bandwidth_khz)
            age = now - spot.last_seen
            alpha = age_alpha(age, window_seconds)
            text = self.ax.text(
                x, y, spot.dx_call, va="center", ha=ha, alpha=alpha, fontsize=8, color=color
            )
            self._texts.append(text)
            self._spot_positions.append((y, spot.dx_call))

    def _on_click(self, event) -> None:
        if event.ydata is None or not self._spot_positions:
            return
        _, call = min(self._spot_positions, key=lambda p: abs(p[0] - event.ydata))
        try:
            self.clipboard_clear()
            self.clipboard_append(call)
        except tk.TclError:
            pass
