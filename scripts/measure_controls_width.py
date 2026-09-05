"""Local-only measurement (no network): how wide does ControlsPanel need
to be, naturally? Used to size the window from real numbers instead of
trial-and-error guessing.
"""

import sys
import tkinter as tk

if sys.platform == "win32":
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass

from spotter_win3.controls import ControlsPanel

root = tk.Tk()
panel = ControlsPanel(
    root,
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
panel.pack()
root.update_idletasks()
print("controls natural width:", panel.winfo_reqwidth())
print("controls natural height:", panel.winfo_reqheight())
root.destroy()
