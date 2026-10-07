# Notifier Slot

The Notifier delivers messages to the Owner. There is one Notifier.

## Contract

- [ ] Send one text message to the Owner.

The core sends one message for each of these events: `spawned`, `respawned` (with its trigger), `input_requested`, `blocked`, `in_review`, `done`, `unblocked`, `system_alert`, `system_recovered`. Dedup and silence are core rules, not Notifier rules: the core sends no message when nothing happened, and never the same message twice. A send failure is logged in `orchestrator.log` and never stops the Cycle. Messages give file paths, with no link base.

`notifier.md` says which tool sends a message, and how.

## Choosing a Notifier

The repo builds only one Notifier: the log file. It is the default, because it needs no account and always works. For a message on your phone or in a chat, fill the Slot in one of two ways:

- **The Host's own messaging.** A Host with a chat, such as KiroCrew or OpenClaw, can already send a message to the Owner. Write a `notifier.md` that names that tool, for example the KiroCrew agent's send-message tool, or `openclaw message send --channel <channel> --target <target> --message "<text>"` for OpenClaw.
- **A messaging MCP server.** Add an MCP server for your chat tool to the Host's agent, and write a `notifier.md` that names its send tool and the target (a channel or a direct message to you).

Either way, the Notifier only sends. It never reads replies: the Owner answers through the Tracker (a Follow-up comment) or the Review System.

## Example notes files

| Example | Notifier |
|---|---|
| [`log-file.md`](log-file.md) | A log file (default, no account) |

## Contract map: `log-file.md`

| Capability | Line in `log-file.md` |
|---|---|
| Send one text message | "Send one message" |
