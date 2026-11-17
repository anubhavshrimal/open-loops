# change-check.md part: Host, OpenClaw

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`openclaw.md`](openclaw.md). Setup copies nothing from it. The Orchestrator never reads `change-check.md`.

## Host

Run one Cycle and return its result: not available. Untested: OpenClaw was not on the test machine. We know no OpenClaw command that runs a job, waits for it and returns its result. So the Change check does not fit this Host yet: keep the scheduled Cycle. When the Host has a command that starts one Cycle, waits for it, and returns its exit code, use the cron example parts as a model.
