# Quickstart

From nothing to your first Task in In Review. Your coding agent does the setup; this page tells you what to expect and what to answer. The words are in [`GLOSSARY.md`](../GLOSSARY.md).

## 1. What you need

- A machine that stays on while you are away: a remote machine, or an always-on local one. The Host, the Runtime and the Workspaces all run on it.
- `git`, `python3`, `timeout` and `crontab`.
- A coding agent with a shell: Claude Code (`claude`) or Codex (`codex`), logged in.
- A Runtime: [Herdr](https://github.com/herdrdev/herdr) (recommended) or `tmux`.
- A project repo with one build and test command (for example `make test` or `npm test`).
- For the defaults: `gh`, logged in (`gh auth status`). Without it, use the local fallbacks.

## 2. Start the Runtime server

Start it from your own shell, not from an agent's shell. (A server that an agent's sandboxed shell starts passes that sandbox to every Worker.)

```sh
tmux new-session -d -s main    # tmux
herdr                          # or Herdr: open it once
```

## 3. Ask your agent to set up Open Loops

```text
Set up Open Loops from https://github.com/anubhavshrimal/open-loops
```

The agent follows [`SETUP.md`](../SETUP.md). It clones the repo to `~/.openloops/open-loops`, checks your machine, shows what it found, and then asks one question at a time. Each question has a recommended answer; say "yes" to take it.

| It asks about | Default | Local fallback (no account) |
|---|---|---|
| Tracker | GitHub Issues (4 labels `ol:ready`, `ol:working`, `ol:blocked`, `ol:in-review`) | Markdown files in `~/.openloops/tasks` |
| Host | cron + `claude -p`, every 30 minutes | the same |
| Runtime | Herdr, if installed | tmux |
| Permission mode | auto mode (read the warning that it shows you) | the same |
| Notifier | log file `~/.openloops/notifications.log` | the same |
| Review System | GitHub PR, opened as a draft | Local branch: the Task branch is the PR |
| Project | the repo in the current directory, its build and test command, Follow-up prefix `ACTION:` | the same |
| Modules | capture, refine, wiki: one yes/no each, default no | the same |

To try Open Loops on one machine with no account, say "use the local fallbacks for every Slot".

Then the agent writes five notes files into `~/.openloops/` (`tracker.md`, `host.md`, `runtime.md`, `notifier.md`, `review.md`), installs the third-party skills, and, with your yes, adds the crontab line.

## 4. Verify with the sample Task

The agent makes the sample Task "Add hello.txt" in Ready, with the Spec [`examples/specs/hello-file.md`](../examples/specs/hello-file.md). Wait for the next Cycle, or let the agent run one Cycle now. Then check:

```sh
tail -n 20 ~/.openloops/notifications.log     # spawned, then in_review
head -n 20 ~/.openloops/orchestrator.log      # one entry for each Cycle, newest first
cat ~/.openloops/state.json                   # the record "ol-hello-file"
tmux ls                                        # or: herdr agent list (the Worker "ol-hello-file")
```

It works when the Task is In Review, the branch `ol-hello-file` has a commit with `hello.txt`, and the Task has a comment that names the PR (GitHub PR) or the branch (Local branch). Then close the sample PR (or delete the branch) and move the Task to Done.

If it does not get there, see [`troubleshooting.md`](troubleshooting.md).

## 5. Your first real Task

1. Write a Spec from a template: [`core/templates/build-spec.md`](../core/templates/build-spec.md) for a known deliverable, [`core/templates/exploration-spec.md`](../core/templates/exploration-spec.md) for an open question. Set `workspace:` to the project repo and `branch:` to the branch to start from. Put the Spec where the Workers can read it (the project repo, `~/.openloops/specs`, or a wiki).
2. Make the Task with a `Spec:` line that gives the Spec's path. Or skip the Spec file and write the Spec in the Task body.
   - **Markdown Tracker:** a file `~/.openloops/tasks/<id>.md`, in the format of [`examples/tasks/hello-file.md`](../examples/tasks/hello-file.md).
   - **GitHub Issues:** an issue with the `Spec:` line in its body.
3. Keep the Task in Backlog while you shape it. Move it to Ready (`state: Ready`, or the label `ol:ready`) when a Worker can do it with no human.
4. Read the result: the PR, and `<repo>/.openloops/<slug>/implementation-notes.html` (what the Worker decided where the Spec was not clear).

## 6. Keep the loop going

- **Review comments:** comment on the PR. The next Cycle respawns the Worker in the same worktree. It fixes the code as new commits and replies to each comment.
- **Follow-up:** comment on the Task with `ACTION: <what to do next>`. The next Cycle respawns the Worker with the full history.
- **Done:** merge the PR yourself (or approve it, or close it). The next Cycle moves the Task to Done.
- **Blocked:** the Worker comments why and moves the Task to Blocked. Fix the cause; the Orchestrator moves the Task back to Ready when it sees that the blocker is gone.

## 7. Stop

Remove the crontab line (or your Host's job), then stop the `ol-` Workers. Details: "Stop and remove" in [`SETUP.md`](../SETUP.md#stop-and-remove). Your worktrees under `<repo>/.openloops/` and the `ol-` branches stay.
