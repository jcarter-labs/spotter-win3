# Improvement queue

Backlog of known, deliberately-deferred issues — not yet fixed. Distinct
from `masterplan-addendum-candidates.md` (which logs process corrections
for the Task 6 addendum, itself currently deferred).

1. **Resize sluggishness.** `BandScope.render()` tears down and rebuilds
   every text/line artist from scratch on every 200ms poll tick,
   regardless of whether data changed. Operator's call: this needs a
   render-path refactor (only redraw on actual data/window change, or
   reuse artists instead of recreating them), not a parameter tweak.
   Deferred during Task 5 remediation.

2. **Declutter label spacing doesn't scale with window height, and
   connector lines get visually tangled under dense clustering.**
   `MIN_LABEL_SPACING` (bandmap.py) is a fixed fraction (0.03) of axes
   height — at the new 1305px-tall window (post aspect-ratio fix) that's
   ~38px between labels, ~3.5x an 8pt font's line height, reading as
   excessive gaps. Separately, connector lines are short fixed-offset
   stubs, not true leader lines back to the tick position, so a tight
   cluster of same-frequency spots (e.g. 10+ POTA spots near one
   frequency) renders as a tangle. Fix: derive spacing from actual
   rendered font size (pixels), not a hardcoded axes-fraction; anchor or
   suppress connector lines under high local density. Found while
   reviewing Screenshot 2026-09-06 131446.png.

3. **No auto-reconnect on cluster disconnect.** If the cluster connection
   drops, `ClusterWorker` exits its loop and status goes red permanently
   — only the Clear button restarts it. Flagged during Task 5
   pressure-testing, not yet fixed.

4. **"Shown" count includes off-window spots.** `Shown: RBN n` counts
   everything currently held in the store for that feed, not just spots
   falling inside the currently-visible frequency window (`in_window`
   filtering only applies to rendering, not to the count). Can make the
   count look inconsistent with what's actually on screen — e.g. non-zero
   "shown" with an empty visible lane right after a band change. Flagged
   during Task 5 remediation verification, not yet fixed.
