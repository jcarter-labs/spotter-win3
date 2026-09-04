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
