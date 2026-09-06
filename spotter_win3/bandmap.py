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

MIN_LABEL_SPACING = 0.03  # fallback fraction, used only before first layout
TICK_HALF_WIDTH = 0.02
FONT_SIZE_PT = 8
LABEL_SPACING_MULTIPLIER = 1.4  # x font line-height, for breathing room
SUBPLOT_TOP = 0.99
SUBPLOT_BOTTOM = 0.02


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
        # Fixed margins, not matplotlib's auto layout. left=0.28 is a
        # measured value, not a guess: at this scope's real composed width
        # (~329px next to the controls panel), a tick label like "14.070"
        # renders at 60px wide, but left=0.2 only reserved ~66px including
        # padding — the label's left edge landed at x=-6.4px, clipping the
        # leading digit. See scripts/measure_tick_labels.py.
        self.figure.subplots_adjust(
            left=0.28, right=0.98, top=SUBPLOT_TOP, bottom=SUBPLOT_BOTTOM
        )

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

        canvas_height_px = self.canvas.get_tk_widget().winfo_height()
        spacing = _label_spacing_fraction(canvas_height_px, self.figure.dpi)

        self._render_lane(
            cluster_spots, center_khz, bandwidth_khz, window_seconds, now, spacing,
            x=0.08, ha="left", color="navy", label_dir=1,
        )
        self._render_lane(
            pota_spots, center_khz, bandwidth_khz, window_seconds, now, spacing,
            x=0.92, ha="right", color="darkgreen", label_dir=-1,
        )

        self.canvas.draw_idle()

    def _render_lane(
        self, spots, center_khz, bandwidth_khz, window_seconds, now, spacing,
        *, x, ha, color, label_dir,
    ) -> None:
        visible = [s for s in spots if in_window(s.freq_khz, center_khz, bandwidth_khz)]
        visible.sort(key=lambda s: s.freq_khz)
        if not visible:
            return

        true_ys = [y_for_freq(s.freq_khz, center_khz, bandwidth_khz) for s in visible]
        display_ys = _declutter(true_ys, spacing)

        spine_x = 0.0 if label_dir == 1 else 1.0
        for spot, true_y, display_y in zip(visible, true_ys, display_ys):
            age = now - spot.last_seen
            alpha = age_alpha(age, window_seconds)
            text = self.ax.text(
                x, display_y, spot.dx_call,
                va="center", ha=ha, alpha=alpha, fontsize=FONT_SIZE_PT, color=color,
            )
            self._artists.append(text)
            self._spot_positions.append((display_y, spot.dx_call))

            if abs(display_y - true_y) > 1e-6:
                # A real leader line from the spine at the true frequency
                # to just before the label at its (possibly nudged)
                # display position — previously a tiny fixed-offset stub
                # near the label itself, which tangled visually once many
                # labels in a tight cluster got spread far apart.
                label_edge_x = x - 0.02 * label_dir
                (line,) = self.ax.plot(
                    [spine_x, label_edge_x],
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


DECLUTTER_UPPER_BOUND = 0.98
DECLUTTER_LOWER_BOUND = 0.02


def _label_spacing_fraction(
    canvas_height_px: float,
    dpi: float,
    font_size_pt: float = FONT_SIZE_PT,
    multiplier: float = LABEL_SPACING_MULTIPLIER,
    subplot_top: float = SUBPLOT_TOP,
    subplot_bottom: float = SUBPLOT_BOTTOM,
) -> float:
    """Minimum label spacing as a fraction of axes height, sized from the
    actual rendered font height in pixels rather than a fixed fraction —
    a fixed fraction (the old MIN_LABEL_SPACING) meant labels looked
    tightly packed in a short window and needlessly sparse in a tall one
    (e.g. ~38px gaps, ~3.5x an 8pt font's line height, at the 1305px-tall
    window from the aspect-ratio fix)."""
    axes_height_px = canvas_height_px * (subplot_top - subplot_bottom)
    if axes_height_px <= 0:
        return MIN_LABEL_SPACING
    font_height_px = font_size_pt * dpi / 72.0
    return (font_height_px * multiplier) / axes_height_px


def _declutter(true_ys: list[float], spacing: float = MIN_LABEL_SPACING) -> list[float]:
    """Greedy minimum-spacing enforcement on a list already sorted
    ascending: pushes a label up just enough to clear the previous one,
    then rescales the whole sequence back inside [0, 1] if that pushed
    labels past the visible range — under heavy spot density, an
    unbounded push sent labels off the top of the plot entirely rather
    than just tightly packed."""
    if not true_ys:
        return []
    adjusted = [true_ys[0]]
    for y in true_ys[1:]:
        prev = adjusted[-1]
        adjusted.append(y if y - prev >= spacing else prev + spacing)

    if adjusted[-1] > DECLUTTER_UPPER_BOUND:
        start = max(DECLUTTER_LOWER_BOUND, adjusted[0])
        span = adjusted[-1] - adjusted[0]
        scale = (DECLUTTER_UPPER_BOUND - start) / span if span > 0 else 1.0
        adjusted = [start + (y - adjusted[0]) * scale for y in adjusted]

    return adjusted
