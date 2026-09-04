"""Launch the real app, let it render and connect for a few seconds, grab a
real screen capture of just its window, then exit — so Claude (no direct
Windows GUI visibility) can actually see the running app.

Uses PIL.ImageGrab (Pillow, already a matplotlib dependency) — a real
screen capture, so the window must be on-screen/foreground when this runs.
"""

import sys
import tkinter as tk

from PIL import ImageGrab

from spotter_win3.main import App

RENDER_DELAY_MS = 15000


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "app_screenshot.png"

    root = tk.Tk()
    app = App(root)
    root.update()  # force geometry to settle before scheduling the capture

    def capture_and_exit():
        # Raw screen capture below — anything else on top of this window at
        # capture time would be swept in too, so force this window to the
        # foreground first (caught spotter-win2's window/terminal bleeding
        # into an earlier capture otherwise).
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
        root.update()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        image.save(out_path)
        print(f"Saved screenshot to {out_path} ({w}x{h} at {x},{y})")
        if app.worker:
            app.worker.stop()
        root.destroy()

    root.after(RENDER_DELAY_MS, capture_and_exit)
    root.mainloop()


if __name__ == "__main__":
    main()
