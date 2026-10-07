# Notifier Slot

The Notifier delivers messages to the Owner. There is one Notifier.

## Contract

- [ ] Send one text message to the Owner.

The core sends one message for each of these events: `spawned`, `respawned` (with its trigger), `input_requested`, `blocked`, `in_review`, `done`, `unblocked`, `system_alert`, `system_recovered`. Dedup and silence are core rules, not Notifier rules. A send failure is logged and never stops the Cycle. Messages give file paths, with no link base.

The repo builds no Notifier other than the log file. The Host's own messaging (KiroCrew, OpenClaw) can fill the Slot, or the Owner can add a messaging MCP server and name its send tool in `notifier.md`.

## Example notes files

| Example | Notifier |
|---|---|
| [`log-file.md`](log-file.md) | A log file (default, no account) |

## Contract map: `log-file.md`

| Capability | Line in `log-file.md` |
|---|---|
| Send one text message | "Send one message" |
