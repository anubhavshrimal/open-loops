# change-check.md part: Host, cron + `claude -p`

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`cron-claude.md`](cron-claude.md). Setup copies the `## Settings` section below into `<home>/change-check.md`. The `## Host` section tells setup how to run the Change check; it is not copied. The Orchestrator never reads `change-check.md`.

## Settings

The runner reads these lines.

- Safety Cycle: 240 minutes
- Error gap: 30 minutes
- Failed Check gap: 30 minutes
- Retry gap: 30 minutes
- Repeat limit: 3
- Transient Change checks: 2
- Reminder: 240 minutes
- Read timeout: 120 seconds

## Host

Run one Cycle and return its result: the command in "How a Cycle starts" of `host.md`, without `cd` and the log redirect. It waits for the Cycle's agent session and returns its exit code: `timeout` ends a hung Cycle with exit 124. Exit 0 means that the session ended, not that the Cycle did all its work (see "Known limit" in `docs/cost-saver.md`).

Crontab line, in place of the one in "How a Cycle starts" (the same `PATH` line). The Change check runs every 5 minutes and starts a Cycle only when it must. While a Cycle runs, each check starts no other Cycle, so a Cycle can take up to its 25-minute `timeout`:

```
*/5 * * * * cd {{HOME_DIR}} && python3 {{CORE_DIR}}/change-check.py check --home {{HOME_DIR}} -- timeout 25m claude -p "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." --model {{ORCHESTRATOR_MODEL}} --permission-mode {{PERMISSION_MODE}} >> {{HOME_DIR}}/host.log 2>&1
```

Check the reads before you switch: `python3 {{CORE_DIR}}/change-check.py test --home {{HOME_DIR}}`. The runner writes one line for each Change check to `{{HOME_DIR}}/change-check.log`. To go back to the fixed interval, put back the crontab line of "How a Cycle starts".
