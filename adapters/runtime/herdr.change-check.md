# change-check.md part: Runtime, Herdr

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`herdr.md`](herdr.md). Setup copies the `## Runtime` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/runtime.md`. The Orchestrator never reads `change-check.md`.

## Runtime

The command only reads. Untested: no Herdr server ran on the test machine. The Herdr TUI has no login, so it has no Auth probe.

### Read: workers

For each `ol-` agent: name and `agent_status`. Gap: a second prompt on an agent that stays `blocked`, and an agent with `agent_status` `unknown`, do not change the output; the Safety Cycle catches them.

```sh
list=$(herdr agent list) || exit 1
printf '%s' "$list" | python3 -c '
import json, sys
agents = json.load(sys.stdin)["result"]["agents"]
print(json.dumps(sorted([a["name"], a.get("agent_status")] for a in agents if str(a.get("name") or "").startswith("ol-"))))'
```
