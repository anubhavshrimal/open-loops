# Host Slot

The Host starts the Orchestrator on a schedule. The Host, the Runtime and the Workspaces are on one machine (a remote machine or an always-on local machine).

## Contract

- [ ] Start the Orchestrator prompt as a new unattended agent session on a schedule (one session per Cycle).
- [ ] Keep a home directory that persists between Cycles.
- [ ] Give the Orchestrator the Owner's tools for the other Slots, plus a shell.
- [ ] Run with no permission prompts (auto or bypass permission mode).
- [ ] Optional, for the Change check: run one Cycle and return its result, with one command that waits for the Cycle's agent session, ends a hung Cycle, and exits with the session's exit code.
- [ ] Optional, for the Change check: run a command with no agent on a schedule.
- [ ] Optional, for the Change check: the Settings of `change-check.md`: Safety Cycle, Error gap, Failed Check gap, Retry gap, Repeat limit, Transient Change checks, Reminder, Read timeout

`host.md` fields:

- [ ] Host name
- [ ] How a Cycle starts (the exact command)
- [ ] Interval (default 30 minutes)
- [ ] Home directory (default `~/.openloops/`)
- [ ] Model and effort of the Orchestrator (a model name, or `default` for the agent's own default model)
- [ ] Permission mode
- [ ] How to stop and remove

Crontab examples wrap the command in `timeout <interval minus 5 minutes>`, so that a hung Cycle cannot pile up.

## Example notes files

| Example | Host |
|---|---|
| [`cron-claude.md`](cron-claude.md) | System cron + `claude -p` (Plain Host) |
| [`cron-codex.md`](cron-codex.md) | System cron + `codex exec` |
| [`kirocrew.md`](kirocrew.md) | KiroCrew scheduled job ("give it the repo link") |
| [`openclaw.md`](openclaw.md) | OpenClaw scheduled job ("give it the repo link") |

With KiroCrew or OpenClaw, the Owner gives that agent the repo link. It follows `SETUP.md` and creates its own scheduled job.

## Second job: wiki-gardener

With the optional wiki module, the Host runs one more scheduled job: the wiki gardener lint prompt (`modules/wiki/gardener/lint.md`), once a day by default. Each example notes file has it under "Second job: wiki-gardener". It uses the same Host capabilities as the Cycle job, so the Host Contract does not change.

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

## Contract map: `cron-codex.md`

| Capability or field | Line in `cron-codex.md` |
|---|---|
| Start a new unattended session on a schedule | "How a Cycle starts": crontab line |
| Home directory that persists | "Home directory" line |
| Tools for the other Slots plus a shell | "How a Cycle starts": "Tools: `codex exec` has a shell" |
| No permission prompts | "Permission mode" line: "`codex exec` never asks for approval" |
| Host name | "Host name" line |
| How a Cycle starts | "How a Cycle starts" command |
| Interval | "Interval" line |
| Model and effort | "Orchestrator model" line, `model_reasoning_effort={{ORCHESTRATOR_EFFORT}}` |
| How to stop and remove | "How to stop and remove" |

## Contract map: `kirocrew.md`

| Capability or field | Line in `kirocrew.md` |
|---|---|
| Start a new unattended session on a schedule | "How a Cycle starts": `kirocrew cron add`, `--no-persistent-session`, `--timeout-secs 1500` |
| Home directory that persists | "Home directory" line |
| Tools for the other Slots plus a shell | "How a Cycle starts": "Tools: a KiroCrew agent has a shell" |
| No permission prompts | "Permission mode" line: `--approval-mode auto` |
| Host name | "Host name" line |
| How a Cycle starts | "How a Cycle starts" command |
| Interval | "Interval" line, `--every 1800` |
| Model and effort | "Orchestrator model" line, `--model {{ORCHESTRATOR_MODEL}}` |
| How to stop and remove | "How to stop and remove": `kirocrew cron pause <id>`, `kirocrew cron remove <id>` |

## Contract map: `openclaw.md`

| Capability or field | Line in `openclaw.md` |
|---|---|
| Start a new unattended session on a schedule | "How a Cycle starts": `openclaw automations add`, `--session isolated` |
| Home directory that persists | "Home directory" line |
| Tools for the other Slots plus a shell | "How a Cycle starts": "Tools: an OpenClaw agent has a shell" |
| No permission prompts | "Permission mode" line: `openclaw exec-policy preset yolo` |
| Host name | "Host name" line |
| How a Cycle starts | "How a Cycle starts" command |
| Interval | "Interval" line, `--cron "*/30 * * * *"` |
| Model and effort | "Orchestrator model" line, `--thinking {{ORCHESTRATOR_EFFORT}}` |
| How to stop and remove | "How to stop and remove": `openclaw automations disable <id>`, `openclaw automations remove <id>` |

## Change check parts

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). Each example notes file has a part of `<home>/change-check.md` next to it, named `<example>.change-check.md`: [`cron-claude.change-check.md`](cron-claude.change-check.md), [`cron-codex.change-check.md`](cron-codex.change-check.md), [`kirocrew.change-check.md`](kirocrew.change-check.md), [`openclaw.change-check.md`](openclaw.change-check.md). Setup copies the part into `<home>/change-check.md` only when the Owner says yes to the cost saver. The Orchestrator never reads it.

## Contract map: `cron-claude.change-check.md`

| Capability | Line in `cron-claude.change-check.md` |
|---|---|
| Run one Cycle and return its result (optional) | "## Host": "Run one Cycle and return its result" |
| Run a command with no agent on a schedule (optional) | "## Host": `change-check.py check` crontab line |
| Settings of `change-check.md` (optional) | "## Settings" list |

## Contract map: `cron-codex.change-check.md`

| Capability | Line in `cron-codex.change-check.md` |
|---|---|
| Run one Cycle and return its result (optional) | "## Host": "Run one Cycle and return its result" |
| Run a command with no agent on a schedule (optional) | "## Host": `change-check.py check` crontab line |
| Settings of `change-check.md` (optional) | "## Settings" list |

## Contract map: `kirocrew.change-check.md`

| Capability | Line in `kirocrew.change-check.md` |
|---|---|
| Run one Cycle and return its result (optional) | "Run one Cycle and return its result: not available" |

## Contract map: `openclaw.change-check.md`

| Capability | Line in `openclaw.change-check.md` |
|---|---|
| Run one Cycle and return its result (optional) | "Run one Cycle and return its result: not available" |
