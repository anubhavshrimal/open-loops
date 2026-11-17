# change-check.md part: Host, KiroCrew

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`kirocrew.md`](kirocrew.md). Setup copies nothing from it. The Orchestrator never reads `change-check.md`.

## Host

Run one Cycle and return its result: not available. `kirocrew cron trigger <id>` starts the Cycle job, but no `kirocrew` command waits for that run and returns its result (checked on the subcommands of `kirocrew cron`: `list`, `add`, `update`, `remove`, `pause`, `resume`, `trigger`, `adopt`, `preview`). So the Change check does not fit this Host yet: keep the scheduled Cycle. When the Host has a command that starts one Cycle, waits for it, and returns its exit code, use the cron example parts as a model.
