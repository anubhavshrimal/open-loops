# notifier.md: log-file Notifier

Example notes file for the Notifier Slot. Copy it to `<home>/notifier.md` and replace each `{{...}}` placeholder.

Notifier: a log file. Each message is one line appended to the file. The Owner reads it (for example with `tail -f`).

Log file: `{{NOTIFIER_LOG}}`

## Send one message

Append one line: the timestamp (ISO 8601 with UTC offset), the event name, then the message text on one line (replace line breaks with spaces).

```sh
printf '%s %s %s\n' "$(date -Iseconds)" "<event>" "<message>" >> {{NOTIFIER_LOG}}
```

Example line:

```
2026-10-06T22:31:04-07:00 spawned 🚀 Picked up: **Add hello.txt** (`ol-hello-file`). Notes: /path/to/repo/.openloops/hello-file/implementation-notes.html
```

If the append fails, log the failure in `orchestrator.log` and continue the Cycle.
