"""Local-only measurement (no network): actual rendered pixel width of the
y-axis tick labels, at the real window size, to size the left margin from
a measurement instead of guessing again.
"""

import sys
import tkinter as tk

if sys.platform == "win32":
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass

from spotter_win3.bandmap import BandScope
from spotter_win3.controls import ControlsPanel

root = tk.Tk()
root.geometry("540x1305+0+0")

body = tk.Frame(root)
body.pack(fill=tk.BOTH, expand=True)

# Replicates main.py's real layout: controls packed first (fixed width),
# then the scope expanding into whatever's left — the isolated
# single-widget measurement was unrealistic (gave it the full window).
controls = ControlsPanel(
    body,
    on_set_band=lambda f: None,
    on_bandwidth_change=lambda b: None,
    on_window_change=lambda w: None,
    on_tier_change=lambda t: None,
    on_clear=lambda: None,
    initial_freq_mhz=14.045,
    initial_bandwidth_khz=50,
    initial_window_min=10,
    initial_tier="regional",
    cluster_name="NC7J (AR-Cluster)",
)
controls.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

scope_column = tk.Frame(body)
scope_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scope = BandScope(scope_column)
scope.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
root.update()

scope.render([], [], 14045.0, 50, 10)
root.update()

canvas_widget = scope.canvas.get_tk_widget()
print("canvas widget width (px):", canvas_widget.winfo_width())
print("canvas widget height (px):", canvas_widget.winfo_height())

renderer = scope.canvas.get_renderer()
for label in scope.ax.get_yticklabels():
    bbox = label.get_window_extent(renderer=renderer)
    print(f"label {label.get_text()!r}: x0={bbox.x0:.1f} x1={bbox.x1:.1f} width={bbox.width:.1f}")

axes_bbox = scope.ax.get_window_extent(renderer=renderer)
print(f"axes left edge (px): {axes_bbox.x0:.1f}")

root.destroy()
