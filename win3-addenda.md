# spotter-win3 masterplan addenda

Consolidated reference for changes to `masterplan-v2.md` — applied and
proposed — so later turns can check here first instead of re-deriving or
re-discovering the same ground. Supersedes the running log previously kept
in `masterplan-addendum-candidates.md` (merged in below); check here going
forward.

## Applied to masterplan-v2.md

**Constitution rule 8 — rewritten by the operator directly (2026-09-06).**

Before: *"Verify UI against the screenshot per element and with pixel
measurements, not memory or impression — measure the running app and
compare it against the screenshot..."*

Now: *"UI verification is a required artifact, not a described action —
the first window-rendering task produces `tools/verify_layout.py`,
measuring rendered geometry against `docs/reference-measurements.json`.
No layout task is complete without a fresh run, pass/fail table pasted as
evidence — not a screenshot."*

Effect: screenshots no longer count as verification evidence for layout
tasks. `tools/verify_layout.py` + `docs/reference-measurements.json` do
not exist yet — build them before the next layout-affecting task, not
retroactively unless asked. Note: Task 5's own wording ("verify per-element
... against the reference screenshot") is now stale relative to this rule;
not fixed, since it's the operator's document.

## Proposed, not yet applied

1. **Step-by-step scope.** Gate single-step confirmation only for
   auth/credential ops or hard-to-reverse third-party actions — not
   reversible local steps (venv creation, version checks, file writes).
   *(Also formalized separately in the global `CLAUDE.md` rewrite this
   session — see that file's "Step, Verify, Step, Verify — scoped".)*

2. **Shared parent-repo trap.** Before git init/remote/commit in a
   subproject, verify `git rev-parse --show-toplevel` matches that
   subproject's own path.

3. **`!`-prefix shell.** Operator-run commands via `!` execute through Git
   Bash on Windows, not PowerShell — use forward-slash/POSIX paths.

4. **Native GUI window inspection.** No direct visibility into a running
   Windows GUI window — use `root.after(...)` + `PIL.ImageGrab.grab()` +
   `winfo_rootx/rooty/width/height`, forced to foreground first (`lift()`,
   `-topmost`, `focus_force()`) so another window can't bleed into the
   capture. Standard verification step for Tk/desktop UI, not ad hoc.
   *(Superseded for layout tasks specifically by the rule 8 rewrite above
   — screenshots remain useful for spot-checking, just not as the
   recorded evidence.)*

5. **"Verify with pixel measurements" was violated across Tasks 3-5** —
   screenshot-eyeballing let a 2.5x aspect-ratio error and a missing
   spec-item-3 control ship as "done." Rule 8's rewrite (above) is the
   direct fix. Process lesson underneath it, still worth keeping: build a
   literal checklist from the spec's enumerated items rather than
   pattern-matching general resemblance to a reference image.

6. **Resolve conflicting instructions by asking, not by silent priority.**
   An operator instruction and a spec/screenshot detail pointing different
   ways must be flagged explicitly, not silently resolved by picking
   whichever reading is more literal or convenient. (Window title vs.
   naming standard; "picker deferred" vs. "control shown in spec item 3
   and the screenshot" both hit this — see prior addenda log for detail
   if needed.)

7. **Diagnostics must use the exact runtime identity, not a stand-in.**
   Every live cluster diagnostic this session hardcoded the operator
   callsign `N6YU` directly. The app itself defaults to `N0CALL` whenever
   `operator_callsign` is unset in config — which it was, the whole
   session. W4MYA (CC-Cluster) silently withholds spot delivery from
   `N0CALL` specifically (connects fine, accepts the filter command,
   never streams a spot) while NC7J/WA9PIE-2/W3LPL all tolerate it —
   confirmed live by testing `ClusterWorker(W4MYA, "N0CALL")` directly:
   status connects, zero spots in 45s, vs. 18-23 spots in the same window
   with `"N6YU"`. This cost multiple live-diagnostic cycles chasing a
   phantom app bug (parser gap, dedup-not-reset — both real and now
   fixed, but neither was *this* problem) before the actual mismatch
   (diagnostic identity ≠ app's actual runtime identity) was checked.
   *Rule proposal:* a diagnostic script must read the same config the app
   reads (or otherwise use the literal value the app would use at
   runtime) for any identity/credential-shaped input, never a hardcoded
   stand-in — a stand-in only proves the stood-in scenario, not the real
   one (this is really rule 7's existing "ask, don't assume" principle,
   applied to test fixtures instead of operator questions).

8. **A cluster profile that depends on a real, non-placeholder identity
   should say so.** W4MYA's dependency on a real callsign is now an
   implicit fact known only via this addendum and the git history. Spec
   item 7 already says "operator callsign ... are configuration inputs,
   not source constants" — worth an explicit follow-on: document
   per-profile identity requirements (if any) in `cluster_profiles.py`'s
   module docstring, which it already does for filter dialects.
