# change-check.md part: Notifier, log file

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`log-file.md`](log-file.md). Setup copies the `## Notifier` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/notifier.md`. The Orchestrator never reads `change-check.md`.

## Notifier

The runner has no agent, so it sends its alerts with this command. It gives the event in `$OL_EVENT` and the message in `$OL_MESSAGE`.

### Send

```sh
printf '%s %s %s\n' "$(date -Iseconds)" "$OL_EVENT" "$OL_MESSAGE" >> {{NOTIFIER_LOG}}
```
