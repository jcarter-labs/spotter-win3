# Improvement queue

Backlog of known issues. Distinct from `win3-addenda.md` (which logs
masterplan changes/process corrections for the Task 6 addendum, itself
currently deferred).

## Open

1. **Resize sluggishness.** `BandScope.render()` tears down and rebuilds
   every text/line artist from scratch on every 200ms poll tick,
   regardless of whether data changed. Operator's call: this needs a
   render-path refactor (only redraw on actual data/window change, or
   reuse artists instead of recreating them), not a parameter tweak.
   Deferred during Task 5 remediation.

## Fixed

2. **Declutter label spacing doesn't scale with window height, and
   connector lines get visually tangled under dense clustering.** Fixed
   in `af92848`: `_label_spacing_fraction()` derives spacing from actual
   rendered font height in pixels instead of a fixed axes-height
   fraction; connector lines now trace from the spine to the label
   instead of a tiny fixed-offset stub. Verified live via screenshot.

3. **No auto-reconnect on cluster disconnect.** Fixed in `335a590`:
   `ClusterWorker._run` now loops with a fixed backoff on connection
   loss instead of exiting permanently, resending the active filter
   commands (tracked via `set_filter_commands()`) after every reconnect.

4. **"Shown" count includes off-window spots.** Fixed in `335a590`:
   counts now filtered through the same `in_window()` check used for
   rendering. Verified live: "Shown: RBN 7 · POTA 19" matched an exact
   manual count of the rendered labels in the same screenshot.
