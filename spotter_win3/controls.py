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
        on_set_band: Callable[[float], str | None],
        on_bandwidth_change: Callable[[int], None],
        on_window_change: Callable[[int], None],
        on_tier_change: Callable[[str], None],
        on_clear: Callable[[], None],
        initial_freq_mhz: float,
        initial_bandwidth_khz: int,
        initial_window_min: int,
        initial_tier: str,
        cluster_name: str,
        cluster_options: list[str] | None = None,
        on_server_change: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_set_band = on_set_band

        tk.Label(self, text="Frequency (MHz)").grid(row=0, column=0, sticky="w")
        self.freq_var = tk.StringVar(value=f"{initial_freq_mhz:.3f}")
        tk.Entry(self, textvariable=self.freq_var, width=10).grid(row=1, column=0)
        tk.Button(self, text="Set", command=self._on_set_clicked).grid(row=1, column=1)

        self.freq_error_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self.freq_error_var, fg="red", font=("TkDefaultFont", 8)).grid(
            row=2, column=0, columnspan=2, sticky="w"
        )

        tk.Label(self, text="Bandwidth (kHz)").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.bandwidth_var = tk.IntVar(value=initial_bandwidth_khz)
        bw = ttk.Combobox(
            self,
            textvariable=self.bandwidth_var,
            values=BANDWIDTH_OPTIONS_KHZ,
            state="readonly",
            width=8,
        )
        bw.grid(row=4, column=0, sticky="w")
        bw.bind("<<ComboboxSelected>>", lambda e: on_bandwidth_change(self.bandwidth_var.get()))

        tk.Label(self, text="Window (min)").grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.window_var = tk.IntVar(value=initial_window_min)
        win = ttk.Combobox(
            self,
            textvariable=self.window_var,
            values=WINDOW_OPTIONS_MIN,
            state="readonly",
            width=8,
        )
        win.grid(row=6, column=0, sticky="w")
        win.bind("<<ComboboxSelected>>", lambda e: on_window_change(self.window_var.get()))

        tk.Label(self, text="Spotter").grid(row=7, column=0, sticky="w", pady=(8, 0))
        self.tier_var = tk.StringVar(value=initial_tier)
        for i, tier in enumerate(("local", "regional")):
            tk.Radiobutton(
                self,
                text=tier.capitalize(),
                variable=self.tier_var,
                value=tier,
                command=lambda: on_tier_change(self.tier_var.get()),
            ).grid(row=8 + i, column=0, sticky="w")

        # Four profiles now wired (NC7J, WA9PIE-2, W3LPL, W4MYA) —
        # switching actually reconnects (see App._on_server_change).
        tk.Label(self, text="Server").grid(row=10, column=0, sticky="w", pady=(8, 0))
        options = cluster_options or [cluster_name]
        self.server_var = tk.StringVar(value=cluster_name)
        server = ttk.Combobox(
            self, textvariable=self.server_var, values=options, state="readonly", width=20
        )
        server.grid(row=11, column=0, columnspan=2, sticky="w")
        if on_server_change is not None:
            server.bind(
                "<<ComboboxSelected>>", lambda e: on_server_change(self.server_var.get())
            )

        tk.Button(self, text="Clear", command=on_clear).grid(
            row=12, column=0, columnspan=2, pady=(12, 0), sticky="ew"
        )

        status_frame = tk.Frame(self)
        status_frame.grid(row=13, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.dot_canvas = tk.Canvas(status_frame, width=12, height=12, highlightthickness=0)
        self.dot_canvas.pack(side=tk.LEFT)
        self._dot = self.dot_canvas.create_oval(2, 2, 10, 10, fill="red")
        self.cluster_status_var = tk.StringVar(value=f"Cluster: {cluster_name}")
        tk.Label(status_frame, textvariable=self.cluster_status_var, fg="gray").pack(
            side=tk.LEFT, padx=(4, 0)
        )

        self.pota_status_var = tk.StringVar(value="POTA: not yet polled")
        tk.Label(self, textvariable=self.pota_status_var, fg="gray").grid(
            row=14, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        self.shown_status_var = tk.StringVar(value="Shown: RBN 0 · POTA 0")
        tk.Label(self, textvariable=self.shown_status_var, fg="gray").grid(
            row=15, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

    def _on_set_clicked(self) -> None:
        text = self.freq_var.get()
        try:
            freq_mhz = float(text)
        except ValueError:
            self.freq_error_var.set(f"'{text}' is not a number")
            return
        error = self._on_set_band(freq_mhz)
        self.freq_error_var.set(error or "")

    def set_status(
        self,
        connected: bool,
        cluster_name: str,
        pota_poll_age_seconds: float | None,
        rbn_shown: int,
        pota_shown: int,
    ) -> None:
        self.dot_canvas.itemconfig(self._dot, fill="green" if connected else "red")
        self.cluster_status_var.set(f"Cluster: {cluster_name}")
        if pota_poll_age_seconds is None:
            self.pota_status_var.set("POTA: not yet polled")
        else:
            self.pota_status_var.set(f"POTA: last poll {int(pota_poll_age_seconds)}s ago")
        self.shown_status_var.set(f"Shown: RBN {rbn_shown} · POTA {pota_shown}")
