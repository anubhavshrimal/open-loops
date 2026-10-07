# Host Slot

The Host starts the Orchestrator on a schedule. The Host, the Runtime and the Workspaces are on one machine (a remote machine or an always-on local machine).

## Contract

- [ ] Start the Orchestrator prompt as a new unattended agent session on a schedule (one session per Cycle).
- [ ] Keep a home directory that persists between Cycles.
- [ ] Give the Orchestrator the Owner's tools for the other Slots, plus a shell.
- [ ] Run with no permission prompts (auto or bypass permission mode).

`host.md` fields:

- [ ] Host name
- [ ] How a Cycle starts (the exact command)
- [ ] Interval (default 30 minutes)
- [ ] Home directory (default `~/.openloops/`)
- [ ] Model and effort of the Orchestrator
- [ ] Permission mode
- [ ] How to stop and remove

Crontab examples wrap the command in `timeout <interval minus 5 minutes>`, so that a hung Cycle cannot pile up.

## Example notes files

| Example | Host |
|---|---|
| [`cron-claude.md`](cron-claude.md) | System cron + `claude -p` (Plain Host) |

## Contract map: `cron-claude.md`

| Capability or field | Line in `cron-claude.md` |
|---|---|
| Start a new unattended session on a schedule | "How a Cycle starts": crontab line |
| Home directory that persists | "Home directory" line |
| Tools for the other Slots plus a shell | "How a Cycle starts": "Tools: `claude -p` has a shell and the Owner's configured MCP servers" |
| No permission prompts | "Permission mode" line, `--permission-mode` in the command |
| Host name | "Host name" line |
| How a Cycle starts | "How a Cycle starts" command |
| Interval | "Interval" line |
| Model and effort | "Orchestrator model" line |
| How to stop and remove | "How to stop and remove" |
