# runtime.md: Herdr Runtime

Example notes file for the Runtime Slot. Copy it to `<home>/runtime.md` and replace each `{{...}}` placeholder.

Runtime: Herdr (https://herdr.dev), a terminal workspace manager for coding agents. Each Worker is one Herdr workspace with one pane, and in that pane one agent named `ol-<slug>`. The `herdr` CLI talks to the Owner's running Herdr server, so the Workers show in the Owner's Herdr session next to the Owner's own Herdr workspaces. A Herdr workspace is a group of panes in Herdr; it is not the Worker's Workspace (the worktree or directory where it works).

Herdr server: the server must already run before a Cycle starts, started by the Owner (open `herdr` once, or run `herdr server`), never by the Orchestrator. A new pane starts from the server's environment, so a server that an agent's shell started passes that agent's sandbox and session variables to every Worker. If `herdr agent list` returns an error, treat it as a Runtime tool failure.

Agent: Claude Code (`claude`), interactive, in auto permission mode. For Codex, see "Codex agent".

Worker model: `{{WORKER_MODEL}}` (`default`: leave out `--model` and its value; the agent then uses its own default model and follows its upgrades)

Cap on live Workers: 5

Workspaces: Herdr makes worktrees itself. In worktree mode, use `herdr worktree create` (see "Spawn a Worker"): it makes the git worktree at the core path `<workspace>/.openloops/worktrees/<slug>` on a new branch `ol-<slug>`, and opens its Herdr workspace and pane, in one call. In directory mode, use `herdr workspace create`.

Runtime ids to store in `state.json`: `{"herdr_workspace_id": "<workspace_id>", "herdr_pane_id": "<pane_id>"}`

Every `herdr` command in this file prints JSON. A failed command prints `{"error": {"code": ..., "message": ...}}`.

## Spawn a Worker

In the commands below, `<workspace>` is the project repo (the Spec's `workspace:`) and `<workspace-path>` is the Worker's Workspace (the worktree, or the directory in directory mode).

1. Open the Workspace and its pane. Pick one of the three cases.

   - Worktree mode, the Workspace does not exist yet. Fetch the start branch and resolve the fork point as the core says, then:

     ```sh
     herdr worktree create --cwd <workspace> --branch ol-<slug> --base "$START_POINT" \
       --path <workspace>/.openloops/worktrees/<slug> --label ol-<slug> --no-focus
     git -C <workspace> remote get-url origin >/dev/null 2>&1 && \
       git -C <workspace>/.openloops/worktrees/<slug> branch --set-upstream-to=origin/<branch>
     ```

   - Worktree mode, the Workspace exists (a Respawn): reuse it. Open a new Herdr workspace in it:

     ```sh
     herdr workspace create --label ol-<slug> --cwd <workspace>/.openloops/worktrees/<slug> --no-focus
     ```

   - Directory mode:

     ```sh
     herdr workspace create --label ol-<slug> --cwd <workspace-path> --no-focus
     ```

   In each case, read `.result.workspace.workspace_id` and `.result.root_pane.pane_id` from the JSON. These are the Runtime ids. If the command returns an error, the spawn failed.

2. Start the agent in that pane. The command waits until the agent is up and ready for input (no `sleep`):

   ```sh
   herdr agent start ol-<slug> --kind claude --pane <pane_id> --timeout 60000 -- \
     --model {{WORKER_MODEL}} --permission-mode {{PERMISSION_MODE}} {{EXTRA_DIRS}}
   ```

   If it returns an error, read the pane (see "Read recent output"). If the pane shows a prompt (for example the folder-trust prompt), the agent is up: answer it as "Send text or keys" says. Otherwise the spawn failed.

3. Write the first prompt to the file `<workspace>/.openloops/<slug>/first-prompt.md` (the state directory already exists), then send it. `herdr agent prompt` sends the text and Enter together. Do not use `--wait`: the Orchestrator does not wait for the Worker's work.

   ```sh
   herdr agent prompt ol-<slug> "$(cat <workspace>/.openloops/<slug>/first-prompt.md)"
   ```

- Build Spec prefix: start the first prompt with `/goal ` (Claude Code's goal command keeps the agent working until the goal is met).
- Exploration Spec with `agent: <name>`: add `--agent <name>` after `--model {{WORKER_MODEL}}`. Claude Code finds the agent file at `{{HOME_DIR}}/.claude/agents/<name>.md` (setup copies `core/agents/<name>.md` there), because `{{EXTRA_DIRS}}` adds the Open Loops home directory with `--add-dir`.
- Effort: add `--effort <level>` after the model to set it.
- Extra directories: `{{EXTRA_DIRS}}` gives the Worker access outside its Workspace to the Tracker files, the home directory and the Spec files, one `--add-dir <path>` for each (for example `--add-dir ~/.openloops --add-dir ~/tasks`).

The agent `ol-<slug>` leaves `herdr agent list` when its process exits, so an absent agent means the Worker exited.

## List Workers with status

```sh
herdr agent list
```

The JSON has `.result.agents`, a list. Keep the agents whose `name` starts with `ol-`. Each agent has `name`, `agent_status`, `workspace_id` and `pane_id`. Read `agent_status` directly; do not guess the status from the output text.

| Core status | How to get it |
|---|---|
| `working` | `agent_status` is `working` |
| `idle` | `agent_status` is `idle` or `done` |
| `Input Request` | `agent_status` is `blocked`: Herdr sees a permission or question prompt |
| `exited` | `ol-<slug>` is not in `herdr agent list` |

If `agent_status` is `unknown`, Herdr cannot classify the agent: read its recent output and judge, as the core says for an unclear status.

To tell the two kinds of Input Request apart, read the output:

- A **tool permission** prompt names a command or file and asks `Do you want to ...?` (for a command, the text `This command requires approval` is above it).
- A **question prompt** has options and no command or file request.

One Worker: `herdr agent get ol-<slug>`.

## Read recent output

```sh
herdr agent read ol-<slug> --source visible --lines 40
```

If the read by agent name fails, read the pane: `herdr pane read <pane_id> --source visible --lines 40`.

## Send text or keys to a live Worker

- Answer an Input Request. Read the menu first: the keys depend on whether its options have numbers.
  - **Numbered menu:** send the digit of the option. The digit selects at once; send no `enter`.
    - one-shot approve: `herdr agent send-keys ol-<slug> 1`
    - deny: the digit of the `No` option (usually `3`; `2` on a two-option prompt)
  - **Menu with no numbers:** move the `❯` cursor with `down` or `up`, then press `enter`. Example, from the first option to the second: `herdr agent send-keys ol-<slug> down enter`.
    - trust the Workspace folder (the folder-trust prompt at start; the cursor starts on `No, exit`): `down`, then `enter`. The Workspace is the Worker's own worktree, so always trust it. Then read the output again: if the first prompt did not land, send it again as step 3 of "Spawn a Worker" says.
  - Never send `2` on a three-option numbered permission prompt: it stores a permanent permission rule. Never choose `No, exit` on the folder-trust prompt: it ends the Worker. Never send `y` or `n` (the menu ignores them). Never send `esc`: it destroys the prompt.
- Send a prompt (for example the gap-fill re-prompt): `herdr agent prompt ol-<slug> "<text>"`. If the agent shows an Input Request, Herdr rejects the prompt; answer the Input Request first.
- Check that a prompt landed: `herdr agent wait ol-<slug> --until working --timeout 10000`. If it does not reach `working`, read the output. If the text sits unsent in the input box, submit it with `herdr agent send-keys ol-<slug> enter` and wait again.
- Wait for the next settled status (the permission-drain loop): `herdr agent wait ol-<slug> --timeout 15000`. It returns at `idle`, `done` or `blocked`.

## Stop a Worker

```sh
herdr workspace close <workspace_id>
```

This closes the Herdr workspace and its pane, and ends the agent process. The worktree and the branch stay. Never run `herdr worktree remove`: the Orchestrator never deletes a Workspace.

## Codex agent

To run Codex (`codex`) Workers instead of Claude Code, change "Spawn a Worker" step 2 to:

```sh
herdr agent start ol-<slug> --kind codex --pane <pane_id> --timeout 60000 -- \
  --model {{WORKER_MODEL}} --sandbox workspace-write --ask-for-approval never -c sandbox_workspace_write.network_access=true {{EXTRA_DIRS}}
```

- Model flag: `--model <model>`. Effort: add `-c model_reasoning_effort=<level>`.
- Auto mode: `--sandbox workspace-write --ask-for-approval never`. Codex then runs commands in its sandbox and never asks for approval, so a Codex Worker rarely shows an Input Request. The sandbox can write only in the Workspace and in each `--add-dir`. `-c sandbox_workspace_write.network_access=true` lets the Worker push its branch and open the PR; with the Local branch Review System you can leave it out. Bypass mode is `--dangerously-bypass-approvals-and-sandbox`: use it only on a machine that is itself a sandbox.
- Extra directories: `{{EXTRA_DIRS}}` uses the same `--add-dir <path>` flag. For Codex, also add the project repo: a commit in a worktree writes into the project repo's `.git` directory, which is outside the sandbox.
- Build Spec prefix: none. Leave it out.
- Exploration Spec with `agent: <name>`: Codex has no agent flag. Start the first prompt with "Act as the agent in `<agents-dir>/<name>.md`." (the path of that agent's instructions file).
- Input Request: read the menu and choose the option that approves this one time; never choose an option that approves for the rest of the session or always.
