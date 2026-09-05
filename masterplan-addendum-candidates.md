# Masterplan addendum candidates (Task 6 input)

Running log of corrections/environment fixes from this build session, for
review at Task 6 (end-of-build addendum). Not yet applied to masterplan-v2.md.

1. **Step-by-step scope.** Only require single-step confirmation for
   operations involving authentication/credentials or hard-to-reverse
   third-party actions — not every reversible local step (venv creation,
   version checks, local file writes).
   *Triggered by:* pausing for confirmation before trivial local commands
   during Task 0.

2. **Shared parent-repo trap.** Before running any git init/remote/commit
   command in a subproject directory, verify `git rev-parse --show-toplevel`
   matches that subproject's own path — a stray parent-level `.git` (e.g. an
   old project's repo rooted at `~/Projects`) can silently make "local"
   git operations affect sibling projects and their remote.
   *Triggered by:* discovering `spotter-win3`'s `git status` was actually
   showing the parent `Projects` repo, with `origin` briefly pointed at the
   wrong GitHub repo before this was caught.

3. **`!`-prefix shell.** Commands given to the operator to run via the `!`
   prefix execute through Git Bash on Windows, not PowerShell — use
   forward-slash or POSIX-style paths, never backslash paths, in any such
   command.
   *Triggered by:* a `!` command with a Windows backslash path failing with
   "No such file or directory" (backslashes stripped as escape characters).

4. **Native GUI window inspection.** Claude has no direct visibility into a
   running native Windows GUI window (unlike a browser page). For Tk apps,
   drive the app's own entry point, add a short `root.after(...)`-scheduled
   capture that calls `root.update()` then `PIL.ImageGrab.grab(bbox=...)`
   using `winfo_rootx/rooty/width/height`, save to a file, then tear the
   window down — Pillow is already a matplotlib dependency, so no new
   install is needed. This should be a standard verification step for any
   Tk/desktop UI task, not an ad hoc one-off.
   *Triggered by:* needing to actually see spotter-win3's window during
   Task 3 (embedded-controls UI) to catch a window-sizing bug (Clear
   button/status line clipped off the right edge) that wasn't visible from
   stdout/exit-code checks alone. See scripts/screenshot_app.py.

5. **"Verify per-element with pixel measurements" (Constitution rule 8) is
   not optional decoration — it was violated for all of Tasks 3-5.** Every
   UI "verification" in this build was: take a screenshot, look at it,
   describe what seemed to match. That is exactly the "memory or
   impression" standard rule 8 prohibits. It let real, measurable defects
   ship as "done": window aspect ratio 1.06 vs. the reference's 0.41 (a
   2.5x difference, only caught when the operator manually compared them),
   and a missing spec-item-3 control (Cluster-server) that a literal
   checklist against the spec text — not a visual scan of the screenshot —
   would have caught immediately.
   *Rule proposal:* before marking any UI task done, (a) open the
   reference image and the actual screenshot with PIL and diff concrete
   numbers (dimensions, aspect ratio) — never eyeball two images
   side-by-side and call it verified; (b) build a literal checklist from
   the spec's enumerated items (e.g. spec item 3's five named controls)
   and confirm each is present, rather than pattern-matching general
   resemblance to the reference image.
   *Triggered by:* operator's own manual pressure-testing after Task 5 was
   declared done, finding the aspect ratio wrong, a missing control, a
   wrong window title, sluggish resize, and a silent crash on bad input —
   all after 46 passing unit tests and multiple "verified live" screenshot
   checks that never caught any of them.

6. **Resolve conflicting instructions by asking, not by silent priority.**
   Two defects this session came from the same root cause: an operator
   instruction and a reference-screenshot detail pointed different ways,
   and screenshot-fidelity was silently allowed to win without flagging
   the conflict. (a) Window title: operator said use "spotter-win3" as
   the naming standard (in response to a config-folder-naming question);
   reference screenshot shows "DX Spotter" in the title bar — never
   surfaced as a conflict, screenshot fidelity won by default. (b)
   Cluster-server control: spec item 7 defers the profile *picker's
   persistence/switching logic* ("only one profile is wired"); spec item
   3 separately lists "Cluster-server" as one of five controls to embed,
   and the reference screenshot shows it present. Read "deferred" as
   license to omit the control from the UI entirely — conflating "don't
   build multi-profile switching" with "don't show the control at all."
   *Rule proposal:* when an instruction and a spec/screenshot detail (or
   two spec items) appear to point different ways, say so explicitly and
   ask which wins — do not silently pick one, even when one reading seems
   more literal or convenient.
   *Triggered by:* operator's pressure-testing catching both; both were
   avoidable by asking a single clarifying question at the time each
   tension was first noticed (both tensions were in fact noticed — the
   title tension was never mentioned at all, and the control tension was
   noticed and resolved wrongly without asking).
