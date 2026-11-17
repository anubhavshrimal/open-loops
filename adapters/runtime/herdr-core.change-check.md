# change-check.md part: Runtime, herdr-core

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`herdr-core.md`](herdr-core.md). Setup copies the `## Runtime` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/runtime.md`. The Orchestrator never reads `change-check.md`.

## Runtime

The command only reads. It does the core check first, so it starts no core. Tested live, read-only, with the Owner's core: stable over 3 runs. herdr-core has no login, so it has no Auth probe.

### Read: workers

For each `ol-` terminal: name, address, status, and whether the agent took its first prompt (`turn` above 0). For a `blocked` Worker, also the kind and the text of its prompt, so a second question with the same status changes the output. Not read: the turn count, the screen, other terminals.

```sh
python3 -c 'import os, socket; s = socket.socket(socket.AF_UNIX); s.connect(os.environ.get("HC_SOCKET") or os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/run/user/%d" % os.getuid(), "herdr-core", (os.environ.get("HC_SESSION") or "default") + ".sock"))' || exit 1
ls=$(hc ls --json) || exit 1
printf '%s' "$ls" | python3 -c '
import json, subprocess, sys
out = []
for t in json.load(sys.stdin)["terminals"]:
    if not str(t.get("name") or "").startswith("ol-"):
        continue
    w = {"name": t["name"], "address": t.get("address"), "status": t.get("status"), "started": (t.get("turn") or 0) > 0}
    if t.get("status") == "blocked":
        p = subprocess.run(["hc", "get", t["address"], "--json"], capture_output=True, text=True)
        if p.returncode:
            sys.exit(p.returncode)
        s = json.loads(p.stdout).get("status") or {}
        w["prompt"] = [s.get("kind"), s.get("msg")]
    out.append(w)
print(json.dumps(sorted(out, key=lambda w: w["name"]), sort_keys=True))'
```
