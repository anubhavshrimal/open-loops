# runtime.md: tmux Runtime

Example notes file for the Runtime Slot. Copy it to `<home>/runtime.md` and replace each `{{...}}` placeholder.

Runtime: tmux, one detached tmux session per Worker, on the Owner's default tmux server. `tmux ls` shows the Workers next to the Owner's own sessions.

tmux server: the default server must already run before a Cycle starts, started from the Owner's own shell (or the Host), never by the Orchestrator. A new session starts from the server's environment, so a server that an agent's sandboxed shell started passes that sandbox to every Worker, and the Workers then fail. If `tmux ls` says that no server is running, treat it as a Runtime tool failure.

Agent: Claude Code (`claude`), interactive, in auto permission mode. For Codex, see "Codex agent".

Worker model: `{{WORKER_MODEL}}` (`default`: leave out `--model` and its value; the agent then uses its own default model and follows its upgrades)

Cap on live Workers: 5

Workspaces: tmux does not make worktrees. The core makes each Workspace as a plain git worktree.

Runtime ids to store in `state.json`: `{"tmux_session": "ol-<slug>"}`

## Spawn a Worker

In the commands below, `<workspace>` is the project repo (the Spec's `workspace:`) and `<workspace-path>` is the Worker's Workspace (the worktree, or the directory in directory mode).

1. Write the first prompt to the file `<workspace>/.openloops/<slug>/first-prompt.md` (the state directory already exists).
2. Start the Worker in a new detached session, named `ol-<slug>`, in the Workspace:

```sh
tmux new-session -d -s ol-<slug> -x 220 -y 50 -c <workspace-path> \
  'claude --model {{WORKER_MODEL}} --permission-mode {{PERMISSION_MODE}} {{EXTRA_DIRS}} "$(cat <workspace>/.openloops/<slug>/first-prompt.md)"'
```

- Build Spec prefix: start the first prompt with `/goal ` (Claude Code's goal command keeps the agent working until the goal is met). If your agent has no such command, leave the prefix out.
- Exploration Spec with `agent: <name>`: add `--agent <name>` after `--model {{WORKER_MODEL}}`. Example for `agent: auto-researcher`: `claude --model {{WORKER_MODEL}} --agent auto-researcher --permission-mode ...`. Claude Code finds the agent file at `{{HOME_DIR}}/.claude/agents/<name>.md` (setup copies `core/agents/<name>.md` there), because `{{EXTRA_DIRS}}` adds the Open Loops home directory with `--add-dir`. That file wins over an agent with the same name in the user-level `~/.claude/agents/`.
- Effort: add `--effort <level>` after the model to set it.
- Extra directories: `{{EXTRA_DIRS}}` gives the Worker access outside its Workspace to the Tracker files, the home directory and the Spec files, one `--add-dir <path>` for each (for example `--add-dir ~/.openloops --add-dir ~/tasks`).

The session ends when the agent process exits, so an absent session means the Worker exited.

## List Workers with status

List: `tmux list-sessions -F '#{session_name}'` and keep the names that start with `ol-`.

Status of one Worker, from its last 40 lines (see "Read recent output"):

- `exited`: the session is not in the list.
- `Input Request`: the output shows an option menu with a `❯` cursor, for example `Do you want to proceed?`, `Do you want to make this edit`, the folder-trust prompt (`Is this a project you created or one you trust?` with `No, exit` and `Yes, I trust this folder`), or any question with options. Some menus number their options (`1.` `2.` ...), some do not.
  - A **tool permission** prompt names a command or file and asks `Do you want to ...?`.
  - A **question prompt** has options and no command or file request.
- `working`: the output shows `esc to interrupt`.
- `idle`: none of the above; the agent shows its empty input box.

## Read recent output

```sh
tmux capture-pane -p -t ol-<slug> -S -40
```

## Send text or keys to a live Worker

- Answer an Input Request. Read the menu first: the keys depend on whether its options have numbers.
  - **Numbered menu:** send the digit of the option, no Enter (the digit selects at once).
    - one-shot approve: `tmux send-keys -t ol-<slug> 1`
    - deny: the digit of the `No` option (usually `3`; `2` on a two-option prompt)
  - **Menu with no numbers:** move the `❯` cursor with `Down` or `Up`, one key per line, then press `Enter`. Example, from the first option to the second: `tmux send-keys -t ol-<slug> Down` then `tmux send-keys -t ol-<slug> Enter`.
    - trust the Workspace folder (the folder-trust prompt at start; the cursor starts on `No, exit`): `Down`, then `Enter`. The Workspace is the Worker's own worktree, so always trust it. After you trust it, read the output again: the agent can drop the first prompt at this step. If the input box is empty and the Worker is not `working`, send the first prompt again from `first-prompt.md` as "Send a prompt" says.
  - Never send `2` on a three-option numbered permission prompt: it stores a permanent permission rule. Never choose `No, exit` on the folder-trust prompt: it ends the Worker. Never send `Escape`: it destroys the prompt.
- Send a prompt (for example the gap-fill re-prompt): write it to a file, paste it, then press Enter:

```sh
tmux load-buffer -b ol-<slug> <file>
tmux paste-buffer -p -d -b ol-<slug> -t ol-<slug>
sleep 1
tmux send-keys -t ol-<slug> Enter
```

- If a first prompt or a pasted prompt sits unsent in the input box, submit it: `tmux send-keys -t ol-<slug> Enter`.
- Wait for the next settled status: read the status every 3 seconds, for up to 15 seconds.

## Stop a Worker

```sh
tmux kill-session -t ol-<slug>
```

This ends the agent process. The Workspace and the branch stay.

## Codex agent

To run Codex (`codex`) Workers instead of Claude Code, change the command in "Spawn a Worker" step 2 to:

```sh
tmux new-session -d -s ol-<slug> -x 220 -y 50 -c <workspace-path> \
  'codex --model {{WORKER_MODEL}} --sandbox workspace-write --ask-for-approval never -c sandbox_workspace_write.network_access=true {{EXTRA_DIRS}} "$(cat <workspace>/.openloops/<slug>/first-prompt.md)"'
```

- Model flag: `--model <model>`. Effort: add `-c model_reasoning_effort=<level>`.
- Auto mode: `--sandbox workspace-write --ask-for-approval never`. Codex then runs commands in its sandbox and never asks for approval, so a Codex Worker rarely shows an Input Request. The sandbox can write only in the Workspace and in each `--add-dir`. `-c sandbox_workspace_write.network_access=true` lets the Worker push its branch and open the PR; with the Local branch Review System you can leave it out. Bypass mode is `--dangerously-bypass-approvals-and-sandbox`: use it only on a machine that is itself a sandbox.
- Extra directories: `{{EXTRA_DIRS}}` uses the same `--add-dir <path>` flag. For Codex, also add the project repo: a commit in a worktree writes into the project repo's `.git` directory, which is outside the sandbox.
- Build Spec prefix: none. Leave it out.
- Exploration Spec with `agent: <name>`: Codex has no agent flag. Start the first prompt with "Act as the agent in `<agents-dir>/<name>.md`." (the path of that agent's instructions file).
- Status: `working` when the output shows `esc to interrupt`; the other status rules are the same.
- Input Request: read the menu and choose the option that approves this one time; never choose an option that approves for the rest of the session or always.
