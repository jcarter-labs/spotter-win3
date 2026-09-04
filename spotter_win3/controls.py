"""Embedded controls panel: Band/Bandwidth/Window/Spotter-tier/Server,
Clear, and the status block (spec item 3). Exact layout/styling is
finalized in the Task 5 UI polish pass against the reference screenshot.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

BANDWIDTH_OPTIONS_KHZ = [10, 20, 40, 50, 80, 100]
WINDOW_OPTIONS_MIN = [1, 5, 10, 30]


class ControlsPanel(tk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        on_set_band: Callable[[float], None],
        on_bandwidth_change: Callable[[int], None],
        on_window_change: Callable[[int], None],
        on_tier_change: Callable[[str], None],
        on_clear: Callable[[], None],
        initial_freq_mhz: float,
        initial_bandwidth_khz: int,
        initial_window_min: int,
        initial_tier: str,
        cluster_name: str,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        tk.Label(self, text="Frequency (MHz)").grid(row=0, column=0, sticky="w")
        self.freq_var = tk.StringVar(value=f"{initial_freq_mhz:.3f}")
        tk.Entry(self, textvariable=self.freq_var, width=10).grid(row=1, column=0)
        tk.Button(
            self, text="Set", command=lambda: on_set_band(float(self.freq_var.get()))
        ).grid(row=1, column=1)

        tk.Label(self, text="Bandwidth (kHz)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.bandwidth_var = tk.IntVar(value=initial_bandwidth_khz)
        bw = ttk.Combobox(
            self,
            textvariable=self.bandwidth_var,
            values=BANDWIDTH_OPTIONS_KHZ,
            state="readonly",
            width=8,
        )
        bw.grid(row=3, column=0, sticky="w")
        bw.bind("<<ComboboxSelected>>", lambda e: on_bandwidth_change(self.bandwidth_var.get()))

        tk.Label(self, text="Window (min)").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.window_var = tk.IntVar(value=initial_window_min)
        win = ttk.Combobox(
            self,
            textvariable=self.window_var,
            values=WINDOW_OPTIONS_MIN,
            state="readonly",
            width=8,
        )
        win.grid(row=5, column=0, sticky="w")
        win.bind("<<ComboboxSelected>>", lambda e: on_window_change(self.window_var.get()))

        tk.Label(self, text="Spotter").grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.tier_var = tk.StringVar(value=initial_tier)
        for i, tier in enumerate(("local", "regional")):
            tk.Radiobutton(
                self,
                text=tier.capitalize(),
                variable=self.tier_var,
                value=tier,
                command=lambda: on_tier_change(self.tier_var.get()),
            ).grid(row=7 + i, column=0, sticky="w")

        tk.Button(self, text="Clear", command=on_clear).grid(
            row=9, column=0, columnspan=2, pady=(12, 0), sticky="ew"
        )

        status_frame = tk.Frame(self)
        status_frame.grid(row=10, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.dot_canvas = tk.Canvas(status_frame, width=12, height=12, highlightthickness=0)
        self.dot_canvas.pack(side=tk.LEFT)
        self._dot = self.dot_canvas.create_oval(2, 2, 10, 10, fill="red")
        self.status_var = tk.StringVar(value=f"Cluster: {cluster_name}")
        tk.Label(status_frame, textvariable=self.status_var, fg="gray").pack(side=tk.LEFT, padx=(4, 0))

    def set_connected(self, connected: bool, shown_count: int, cluster_name: str) -> None:
        self.dot_canvas.itemconfig(self._dot, fill="green" if connected else "red")
        state = "connected" if connected else "disconnected"
        self.status_var.set(f"{cluster_name}: {state} · shown {shown_count}")
