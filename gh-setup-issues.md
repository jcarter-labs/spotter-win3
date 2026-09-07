# GitHub/Git Setup Issues — Task 0 (spotter-win3)

Log of problems hit while resolving Task 0's "repo name and visibility"
requirement, with recommended masterplan additions. Feeds Task 6
(end-of-build addendum) alongside `win3-addenda.md`.

## Issues encountered

### 1. Shared parent-repo trap
`spotter-win3/` had no `.git` of its own. `git status`/`git remote` run from
inside it were silently operating on `C:\Users\johnn\Projects\.git` — the old
`spot_filter` project's repo, whose working tree covers every sibling
directory (`spotter-win1/`, `spotter-win2/`, `Spotter/`, `audio_amp/`,
`k4-plot/`, etc.). Not caught until `git status` output showed `../`-relative
paths outside spotter-win3.

**Risk:** a commit/push from here would have pushed every sibling project's
files into the `spotter-win3` GitHub repo.

### 2. Origin mis-pointed on the parent repo
Before the trap above was noticed, `git remote set-url origin` was run
against that same shared repo, pointing the *parent* `Projects` repo's
`origin` at `jcarter-labs/spotter-win3` — wrong target, and briefly left the
`spot_filter` repo's remote misconfigured.

**Remediation applied:** initialized a standalone `.git` inside
`spotter-win3/` (verified via `git rev-parse --show-toplevel`), pointed its
own `origin` at `jcarter-labs/spotter-win3`, and restored the parent repo's
`origin` back to `spot_filter`.

### 3. Classifier blocked the parent-repo fix
The command to restore the parent repo's `origin` was denied by the Claude
Code auto-mode classifier (modifying git config outside the current
subproject's scope). Required the operator to run it directly via the `!`
bash-input mechanism instead.

### 4. `!`-prefix path syntax
The first `!`-prefixed remediation command used a Windows backslash path
(`C:\Users\johnn\Projects`) and failed — `!` executes via Git Bash on this
machine (not PowerShell), which strips backslashes as escape characters,
producing `C:UsersjohnnProjects`. Fixed by switching to forward-slash paths.

### 5. Repo existence/visibility resolved by verification, not inference
The masterplan requires repo name/visibility "resolved and verified with
real output." An early conversational answer ("yes") to a compound
create-vs-exists question was ambiguous. Rather than assume, ran
`gh repo view spotter-win3 --json name,visibility,url,owner` to get ground
truth (repo already existed, private, under `jcarter-labs`) before touching
any remote.

## Recommended masterplan additions

1. **Repo-root guard.** Before any git init/remote/add/commit/push in a
   subproject directory, run `git rev-parse --show-toplevel` and confirm it
   equals that subproject's own absolute path. If it resolves to a parent or
   sibling directory instead, stop and report before any further git command.

2. **Verify repo state, don't infer it.** Repo existence/visibility must come
   from a live `gh repo view --json ...` (or equivalent), not from a
   conversational yes/no — especially when the operator may have created or
   changed it outside the session.

3. **Cross-scope git operations route through the operator.** When a git or
   gh command targets a path outside the current subproject (e.g. undoing a
   mistake made against a shared parent repo) and is blocked by the
   permission classifier, hand the operator the exact command rather than
   retrying or seeking an in-band "exception" — an in-conversation grant
   doesn't lift a classifier-level block.

4. **`!`-prefixed commands use POSIX-style paths.** Any command written for
   the operator to run via `!` must use forward-slash or `/c/...`-style
   paths on Windows, since it executes through Git Bash regardless of the
   session's primary shell.

(See `win3-addenda.md` for the non-gh-specific candidates, including
step-by-step confirmation scoped to auth/credential operations only.)
