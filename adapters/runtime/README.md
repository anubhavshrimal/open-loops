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
- [ ] The agent start command, model flags and extras (the Build Spec prefix, the option that starts the Exploration Worker agent for an Exploration Spec).
- [ ] The keys that answer an Input Request (one-shot approve, deny) and the keys never to send.
- [ ] The Runtime ids to store in `state.json`.
- [ ] Whether the Runtime makes worktrees itself. If not, the core makes each Workspace as a plain git worktree at `<repo>/.openloops/worktrees/<slug>`.
- [ ] The cap on live Workers (default 5).

Rules that the core applies to every Runtime: Worker names are `ol-<slug>`; a Workspace is never force-overwritten; Workers run in auto or bypass permission mode.

## Example notes files

| Example | Runtime |
|---|---|
| [`tmux.md`](tmux.md) | tmux with Claude Code (local fallback) |

## Contract map: `tmux.md`

| Capability | Line in `tmux.md` |
|---|---|
| Spawn a named Worker (agent, model, directory, first prompt) | "Spawn a Worker" |
| List the Workers with status | "List Workers with status" |
| Read recent output | "Read recent output" |
| Send text or keys | "Send text or keys to a live Worker" |
| Stop a Worker | "Stop a Worker" |
| Core statuses | "List Workers with status": the four status rules |
| Agent, model, extras | "Agent", "Worker model", "Build Spec prefix", `--agent <name>` |
| Input Request keys | "Send text or keys to a live Worker": "one-shot approve", "deny", "Never send" |
| Runtime ids | "Runtime ids to store in `state.json`" |
| Worktrees | "Workspaces" line |
| Cap | "Cap on live Workers" line |
