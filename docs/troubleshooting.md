# Troubleshooting

Start with the three files in the home directory (default `~/.openloops/`):

| File | What it tells you |
|---|---|
| `orchestrator.log` | One entry for each Cycle, newest first: what the Orchestrator found, did, and why. |
| `host.log` | The raw output of each Cycle (cron Hosts). Errors before the Cycle could log anything are here. |
| `state.json` | The live Worker records and the open alerts. |

Then read the Notifier (default `~/.openloops/notifications.log`), and the Worker's `<repo>/.openloops/<slug>/implementation-notes.html`.

## No Cycle runs

**Symptom:** `orchestrator.log` gets no new entry.

- Check the schedule: `crontab -l` shows a line with "Run one Open Loops Cycle" (or your Host's job list shows the job).
- Check `host.log`. `command not found` means that cron's short `PATH` does not have the agent CLI: set the `PATH=` line above the crontab line (see "How a Cycle starts" in `host.md`).
- Run the command from "How a Cycle starts" in `host.md` once by hand. Any error is now on your screen.
- A Cycle that hangs is ended by `timeout` 5 minutes before the next one. If every Cycle ends this way, look at the last entry in `host.log` for the step that hangs (often a shell command that waits for input, for example a `cp -i` alias).

## One alert, then nothing

**Symptom:** one `system_alert` message, then silence. `state.json` has an `alerts` entry.

This is by design: one alert for each outage, and each Cycle stops with no change until the Slot's tools work again. Fix the cause in the message (a missing notes file, `gh` logged out, the Tracker directory not readable, no Runtime server). The next Cycle sends `system_recovered` and goes on. Do not delete the `alerts` entry by hand unless you have fixed the cause.

## A Ready Task is not picked up

Look for the Task's name in the newest `orchestrator.log` entry.

| Log says | Cause | Fix |
|---|---|---|
| `no spec for task <id>` | No `Spec:` line and no Spec text in the body. | Add a `Spec:` line or write the Spec in the body. |
| `<task> gated by <upstream> (state: ...)` | An upstream Task is not Done. In Review does not count. | Wait, or move the upstream Task to Done. |
| `<parent>: no eligible child this Cycle` | It is a parent Task. Only leaf Tasks spawn. | Move a child Task to Ready. |
| `<child> deferred.` | The Spec has `spec_status: deferred`. | Set `spec_status: ready`. |
| Tasks stay in Ready at the cap | The cap of live Workers (default 5) is full. | Wait, or raise the cap in `runtime.md`. |
| Nothing about the Task | The Task is not in Ready in the Tracker's native form. | Check the state map in `tracker.md` (for GitHub Issues: exactly one label `ol:ready` on an open issue). |

## A Worker does not start, or starts and does nothing

- **No Runtime server.** tmux: `tmux ls` must list a server. Herdr: `herdr agent list` must answer. Start the server from your own shell.
- **Workers fail at once, with sandbox or permission errors.** The Runtime server was started from an agent's sandboxed shell, so every Worker gets that sandbox. Stop the server and start it again from your own shell.
- **The worktree was not made.** The log says why. Often the branch `ol-<slug>` already exists from manual git work. Open Loops never force-overwrites: delete or rename that branch yourself, or rename the Spec file (a new slug).
- **The first prompt sits unsent in the Worker's input box.** The Orchestrator checks for this right after the spawn and submits it. If it stays, attach (`tmux attach -t ol-<slug>`) and press Enter.
- **The Worker waits on the folder-trust prompt.** The Orchestrator answers it. If the Worker exited instead, check that `runtime.md` was not changed in its "Never send" lines.
- **An Exploration Spec fails with an unknown agent.** The agent file is missing: `<home>/.claude/agents/auto-researcher.md` must exist (setup copies it from `core/agents/`), and `runtime.md` must add the home directory with `--add-dir`.

## A Worker waits on a prompt

**Symptom:** an `input_requested` message: "Permission needed" or "Question".

The Orchestrator answers a prompt only when it is safe and the Spec makes the answer clear. Otherwise it waits for you. Attach to the Worker (`tmux attach -t ol-<slug>`, or open Herdr) and answer it. If the same kind of prompt comes back often, settle it in your agent's permission settings, or add the answer to the Spec.

## The Task did not reach In Review

- Read the Worker's last output (`tmux capture-pane -p -t ol-<slug> -S -60`, or Herdr), its Tracker comment, and its `implementation-notes.html`.
- **Blocked:** the Worker explains why in its Tracker comment. Fix the cause. The Orchestrator moves the Task back to Ready when it sees that the blocker is gone, or move it yourself.
- **The build and test command fails.** The Worker must pass it before it opens a PR. Check the command in the "Projects" table of `review.md`.
- **The review skill is missing.** Setup installs `code-review` from mattpocock/skills. Run `./install-third-party.sh` from the clone again.
- **`git push` fails (GitHub PR).** Check `gh auth status` and the remote in `review.md`. With the Local branch Review System, no Worker pushes: the branch in the project repo is the PR.

## A Review comment or Follow-up gives no Respawn

- The Task must be In Review (or Ready, for a Follow-up).
- A Follow-up must start with the prefix in `tracker.md` (default `ACTION:`), exactly, at the start of the comment. Case matters.
- A Review comment gives one Respawn. The Orchestrator remembers the last comment id it acted on (`review_state.last_comment_id`), so a new comment is needed for the next Respawn.
- If a Worker for the Task is still live, the Orchestrator waits for it to finish first.
- With the Local branch Review System, Review comments are Tracker comments with the Follow-up prefix.

## A Task does not move to Done

- GitHub PR: the PR must be approved, merged or closed. A draft PR with no review stays In Review.
- Local branch: the Worker's last commit must be in `main` (`git merge-base --is-ancestor <sha> main`), or move the Task to Done yourself.
- A pending Follow-up keeps the Task open until a Worker fulfils it.

## Too many messages, or none

- No message when nothing happened is by design (silent mode).
- No messages at all: check `notifier.md`. A send failure is logged in `orchestrator.log` and never stops the Cycle, so look there.
- The same message twice is a bug: report it with the two `orchestrator.log` entries.

## Clean start for one Task

Open Loops never deletes a Workspace: a Respawn always continues the prior work. For a clean start, stop the Worker, delete its worktree yourself (`git worktree remove <repo>/.openloops/worktrees/<slug>`), rename the Spec file so that the Task gets a new slug, and move the Task to Ready. The old branch `ol-<slug>` stays until you delete it.
