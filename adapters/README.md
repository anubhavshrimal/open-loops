# Adapters

An Adapter is the Owner's own tools for one Slot, plus the notes file that tells the Orchestrator how to use them. Each Slot directory holds that Slot's Contract (its `README.md`) and example notes files.

| Slot | Notes file | Contract | Examples |
|---|---|---|---|
| Tracker | `tracker.md` | [tracker/README.md](tracker/README.md) | [GitHub Issues](tracker/github-issues.md) (default), [Markdown](tracker/markdown.md) (fallback) |
| Host | `host.md` | [host/README.md](host/README.md) | [cron + `claude -p`](host/cron-claude.md), [cron + `codex exec`](host/cron-codex.md), [KiroCrew](host/kirocrew.md), [OpenClaw](host/openclaw.md) |
| Runtime | `runtime.md` | [runtime/README.md](runtime/README.md) | [Herdr](runtime/herdr.md) (recommended), [tmux](runtime/tmux.md) |
| Notifier | `notifier.md` | [notifier/README.md](notifier/README.md) | [log file](notifier/log-file.md) |
| Review System | `review.md` | [review/README.md](review/README.md) | [GitHub PR](review/github-pr.md) (default), [Local branch](review/local-branch.md) (fallback) |

To use an example, copy it into the Open Loops home directory (default `~/.openloops/`) under the notes file name, and replace each `{{...}}` placeholder with your own value. The Orchestrator reads the five notes files at the start of each Cycle.
