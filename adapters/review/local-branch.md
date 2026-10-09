# review.md: Local branch Review System

Example notes file for the Review System Slot. Copy it to `<home>/review.md` and replace each `{{...}}` placeholder.

Review System: Local branch. There is no hosting service. The "PR" is the Task branch `ol-<slug>` in the project repo.

Remote to push to: none. The Local branch never pushes: the Workspace is a git worktree of the project repo, so every commit on `ol-<slug>` is already in the project repo. Never run `git push`.

Open PRs as: draft (the Local branch has no draft state; the setting has no effect here)

Review rounds: new commits

AI disclosure: off

Review skill: `code-review` (from mattpocock/skills)

## Projects

| Project repo | Build and test command |
|---|---|
| `{{PROJECT_REPO}}` | `{{BUILD_TEST_COMMAND}}` |

## Worker capabilities

- **Publish a branch:** nothing to do. Commit on `ol-<slug>` in the Workspace; the branch is already in the project repo.
- **Open a PR:** post a Tracker comment on the Task that names the branch (`Branch: ol-<slug>`), the latest commit SHA, and a summary. That comment is the PR.
- **PR reference** (the form to put in Tracker comments): `Branch: ol-<slug>`
- **Publish more commits:** commit on the same branch. There is nothing to push.
- **Reply to a Review comment:** post a Tracker comment that starts with `Re <comment-id>:` and says what you did (with the commit SHA), or why you push back.
- **Checks:** run the project's build and test command from the table above in the Workspace before each PR comment. Put the result in the Tracker comment as `Checks: pass` or `Checks: fail`, with the failing output.

## Orchestrator capabilities

All git commands run in the project repo, `git -C <project repo> ...`.

- **Read PR state:**
  - `open`: the branch `ol-<slug>` exists and has commits that are not in `main` (`git log --oneline main..ol-<slug>` is not empty).
  - `merged`: the commit SHA in the Worker's latest PR comment is in `main` (`git merge-base --is-ancestor <sha> main` exits 0).
  - `approved`: the Owner moved the Task to Done.
  - `closed`: the branch `ol-<slug>` no longer exists and was not merged.
- **Read Review comments with ids:** the Task's Tracker comments that start with the Follow-up prefix (see `tracker.md`) and were posted after the latest PR comment. The id is the Tracker comment id. Here a Review comment and a Follow-up are the same comment: treat it as one signal.
- **Read Checks:** the `Checks:` line in the Worker's latest Tracker comment. No `Checks:` line means pending.

## Triggers

- New Review comment, or `Checks: fail` → Respawn.
- `merged` or `approved` → Done.
- `closed` without merge → Done.
