# Runtime Slot

The Runtime spawns, watches and stops Workers. All Workers, the Host and the Workspaces are on one machine.

## Contract

A Runtime must supply all five:

- [ ] Spawn a named Worker, with an agent, a model, a directory and a first prompt.
- [ ] List the Workers, each with its status.
- [ ] Read a Worker's recent output.
- [ ] Send text or keys to a live Worker.
- [ ] Stop a Worker.

`runtime.md` also says:

- [ ] How to get each core status: `working`, `idle`, `Input Request`, `exited`.
- [ ] The agent start command, model flags (a model name, or `default`, which leaves the model flag out) and extras (the Build Spec prefix, the option that starts the Exploration Worker agent for an Exploration Spec).
- [ ] The keys that answer an Input Request (one-shot approve, deny) and the keys never to send.
- [ ] The Runtime ids to store in `state.json`.
- [ ] Whether the Runtime makes worktrees itself. If not, the core makes each Workspace as a plain git worktree at `<repo>/.openloops/worktrees/<slug>`.
- [ ] The cap on live Workers (default 5).

Rules that the core applies to every Runtime: Worker names are `ol-<slug>`; a Workspace is never force-overwritten; Workers run in auto or bypass permission mode.

## Example notes files

| Example | Runtime |
|---|---|
| [`herdr.md`](herdr.md) | Herdr with Claude Code or Codex (recommended) |
| [`tmux.md`](tmux.md) | tmux with Claude Code or Codex (local fallback) |

Each example starts Claude Code Workers, and its "Codex agent" section gives the lines for Codex Workers.

## Contract map: `herdr.md`

| Capability | Line in `herdr.md` |
|---|---|
| Spawn a named Worker (agent, model, directory, first prompt) | "Spawn a Worker": `herdr agent start ol-<slug>`, `herdr agent prompt ol-<slug>` |
| List the Workers with status | "List Workers with status": `herdr agent list` |
| Read recent output | "Read recent output": `herdr agent read ol-<slug> --source visible --lines 40` |
| Send text or keys | "Send text or keys to a live Worker": `herdr agent send-keys ol-<slug> 1` |
| Stop a Worker | "Stop a Worker": `herdr workspace close <workspace_id>` |
| Core statuses | "List Workers with status": the table that maps `agent_status` to each core status |
| Agent, model, extras | "Agent", "Worker model", "Build Spec prefix", `--agent <name>`, "Codex agent" |
| Input Request keys | "Send text or keys to a live Worker": "one-shot approve", "deny", "Never send" |
| Runtime ids | "Runtime ids to store in `state.json`" |
| Worktrees | "Herdr makes worktrees itself", `herdr worktree create` |
| Cap | "Cap on live Workers" line |

## Contract map: `tmux.md`

| Capability | Line in `tmux.md` |
|---|---|
| Spawn a named Worker (agent, model, directory, first prompt) | "Spawn a Worker" |
| List the Workers with status | "List Workers with status" |
| Read recent output | "Read recent output" |
| Send text or keys | "Send text or keys to a live Worker" |
| Stop a Worker | "Stop a Worker" |
| Core statuses | "List Workers with status": the four status rules |
| Agent, model, extras | "Agent", "Worker model", "Build Spec prefix", `--agent <name>`, "Codex agent" |
| Input Request keys | "Send text or keys to a live Worker": "one-shot approve", "deny", "Never send" |
| Runtime ids | "Runtime ids to store in `state.json`" |
| Worktrees | "Workspaces" line |
| Cap | "Cap on live Workers" line |
