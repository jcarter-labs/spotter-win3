"""Reproduces the exact bug scenario: start on one cluster, let it
accumulate dedup state, then switch to another (mimicking the Server
dropdown) — before the fix, calls already seen on the first server
within the last 2 minutes would be silently suppressed as "duplicates"
on the second, even though DedupCache is keyed only on (call, band),
not on which server/feed reported them.
"""

import sys
import tkinter as tk

from PIL import ImageGrab

from spotter_win3.main import App

FIRST_SERVER = "WA9PIE-2 (DXSpider)"
SECOND_SERVER = "W4MYA (CC-Cluster)"
SETTLE_MS = 12000
POST_SWITCH_MS = 40000


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "app_screenshot.png"

    root = tk.Tk()
    app = App(root)
    root.update()

    def switch_server():
        print(f"Dedup entries before switch: {len(app.dedup._seen)}")
        app._on_server_change(SECOND_SERVER)
        print(f"Dedup entries after switch (should be 0): {len(app.dedup._seen)}")
        root.after(POST_SWITCH_MS, capture_and_exit)

    def capture_and_exit():
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
        root.update()
        x, y = root.winfo_rootx(), root.winfo_rooty()
        w, h = root.winfo_width(), root.winfo_height()
        image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        image.save(out_path)
        print(f"Saved screenshot to {out_path} ({w}x{h} at {x},{y})")
        print(f"Final: RBN spots stored = {len(app.store.spots_for_feed('cluster'))}")
        if app.worker:
            app.worker.stop()
        root.destroy()

    app._on_server_change(FIRST_SERVER)
    root.after(SETTLE_MS, switch_server)
    root.mainloop()


if __name__ == "__main__":
    main()
