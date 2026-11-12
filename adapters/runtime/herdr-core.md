# runtime.md: herdr-core Runtime

Example notes file for the Runtime Slot. Copy it to `<home>/runtime.md` and replace each `{{...}}` placeholder.

Runtime: herdr-core (https://herdr.dev), the server behind the Herdr app, driven with its CLI `hc`. Each Worker is one hc terminal named `ol-<slug>`, with one agent in it. The `hc` CLI talks to the Owner's running core, so the Workers show in the Owner's Herdr app (or in any shell with `hc`, or `hc attach <address>`) next to the Owner's own terminals. hc is not `herdr`, the Herdr TUI: the two do not share agents.

Core: the core must already run before a Cycle starts, started by the Owner from their own shell (`hc server start`, or open the Herdr app), never by the Orchestrator. A new terminal starts from the core's environment, not from the environment of the shell that runs `hc`, so a core that an agent's shell started passes that agent's sandbox and session variables to every Worker. Any `hc` command starts a core when none runs, so do the core check below before any other `hc` command.

Core check, once per Cycle, before any other `hc` command. It connects to the core's socket, and it starts no core:

```sh
python3 -c 'import os, socket; s = socket.socket(socket.AF_UNIX); s.connect(os.environ.get("HC_SOCKET") or os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/run/user/%d" % os.getuid(), "herdr-core", (os.environ.get("HC_SESSION") or "default") + ".sock"))'
```

- Exit 0: the Owner's core runs. Go on with the `hc` commands below.
- Any other exit: no core answers. Treat it as a Runtime tool failure, and run no `hc` command in this Cycle.
- The socket is at `$XDG_RUNTIME_DIR/herdr-core/<session>.sock` (`/run/user/<uid>/...` when `XDG_RUNTIME_DIR` is not set, as in cron). If the Owner's core keeps it at another place, `hc` names both paths in its error text: set `HC_SOCKET` to the core's path in the Host's environment.
- Never run `hc server start`, `hc server stop` or `hc server restart`.

Agent: Claude Code (`claude`), interactive, in auto permission mode. For Codex, see "Codex agent". Give the agent as an absolute path, `"$(command -v claude)"`: the shell of the Orchestrator expands it to the path in its own `PATH`, and the core's `PATH` can be different.

Worker model: `{{WORKER_MODEL}}` (`default`: leave out `--model` and its value; the agent then uses its own default model and follows its upgrades)

Cap on live Workers: 5

Workspaces: hc does not make worktrees. The core makes each Workspace as a plain git worktree. Give absolute paths: `git -C <workspace> worktree add -b ol-<slug> <workspace>/.openloops/worktrees/<slug> "$START_POINT"`.

Runtime ids to store in `state.json`: `{"hc_address": "<address>"}` (for example `{"hc_address": "t7"}`). A name is unique only among live terminals: a stopped Worker keeps its name until `hc rm`, and a new Worker can get the same name with a new address. So use the address in every command below, and use the name only to find a live Worker that has no record yet.

Every `hc` command in this file prints JSON when its output goes to a pipe or a file, except `hc read` (text). Add `--json` to be sure. A failed command prints `{"error": {"kind": ..., "message": ..., "hint": ...}}` on stderr and exits with a code that is not 0 (3 not found, 5 unavailable, 9 blocked, 11 finished).

## Spawn a Worker

In the commands below, `<workspace>` is the project repo (the Spec's `workspace:`) and `<workspace-path>` is the Worker's Workspace (the worktree, or the directory in directory mode).

1. Write the first prompt to the file `<workspace>/.openloops/<slug>/first-prompt.md` (the state directory already exists).
2. Start the Worker in a new terminal, named `ol-<slug>`, in the Workspace, with the first prompt as the agent's first argument:

   ```sh
   hc run --bg --json --name ol-<slug> --cwd <workspace-path> --no-parent --outlive-parent --no-notify \
     "$(command -v claude)" --model {{WORKER_MODEL}} --permission-mode {{PERMISSION_MODE}} {{EXTRA_DIRS}} \
     "$(cat <workspace>/.openloops/<slug>/first-prompt.md)"
   ```

   Read `.address` from the JSON (for example `t7`). This is the Runtime id. If the command returns an error, the spawn failed. `--no-parent` and `--outlive-parent` keep the Worker alive after the Orchestrator's session ends. `--no-notify` stops hc from typing notes into the Orchestrator.

3. Check that the first prompt landed: `hc get <address> --json`. The prompt is in the agent's arguments. With no start prompt, it runs by itself when the agent is up; do not send it a second time while the agent starts.
   - Landed: `.status.state` is `working`, or `.turn` is `1` or more.
   - Starting: `.turn` is `0` and `.status` is `null` or `.status.state` is `idle`. hc reports `idle` at turn 0 before the agent has taken its first prompt, so this is not `idle`. Read the output (see "Read recent output"). If it shows the folder-trust prompt, answer it as "Send text or keys" says. Otherwise check again after 5 seconds, for up to 30 seconds.
   - After a start prompt (for example the folder-trust prompt), the agent often drops the first prompt. If the agent is up (its empty input box shows), `.turn` is still `0`, and the first prompt is not in the output, the prompt did not land: send it as "Send a prompt" says.

- Build Spec prefix: start the first prompt with `/goal ` (Claude Code's goal command keeps the agent working until the goal is met).
- Exploration Spec with `agent: <name>`: add `--agent <name>` after `--model {{WORKER_MODEL}}`. Example for `agent: auto-researcher`: `"$(command -v claude)" --model {{WORKER_MODEL}} --agent auto-researcher --permission-mode ...`. Claude Code finds the agent file at `{{HOME_DIR}}/.claude/agents/<name>.md` (setup copies `core/agents/<name>.md` there), because `{{EXTRA_DIRS}}` adds the Open Loops home directory with `--add-dir`.
- Effort: add `--effort <level>` after the model to set it.
- Extra directories: `{{EXTRA_DIRS}}` gives the Worker access outside its Workspace to the Tracker files, the home directory and the Spec files, one `--add-dir <path>` for each (for example `--add-dir ~/.openloops --add-dir ~/tasks`).

When the agent process exits, its terminal is `finished` and leaves `hc ls`, so an absent Worker means the Worker exited.

## List Workers with status

```sh
hc ls --json
```

The JSON has `.terminals`, a list of the live terminals of the Owner's core. Keep the terminals whose `name` starts with `ol-`. Each has `address`, `name`, `state` (`live`), `turn`, and `status` (`working`, `idle`, `done`, `blocked` or `error`; absent when hc has no status for it). Match a Worker to its `state.json` record by `address`. Read `status` directly; do not guess the status from the output text, except where the table says so.

| Core status | How to get it |
|---|---|
| `working` | `status` is `working`; or `turn` is `0` and `status` is `idle` or absent (the agent is starting) |
| `idle` | `status` is `idle` or `done`, and `turn` is `1` or more |
| `Input Request` | `status` is `blocked`: the agent shows a permission or question prompt |
| `exited` | the record's address is not in `hc ls` |

- No `status` at turn 0 is also what the folder-trust prompt shows: read the output. If it shows a menu, it is an `Input Request`.
- If a Worker is still at turn 0 and its record's `started` is more than 10 minutes ago, read the output. If the agent shows its empty input box and the first prompt is not in the output, send the first prompt again as "Send a prompt" says.
- If `status` is `error`, or absent at turn 1 or more, hc cannot classify the agent: read its recent output and judge, as the core says for an unclear status.

To tell the two kinds of Input Request apart, get the Worker: `hc get <address> --json`. `.status.kind` is `permission` or `question`, and `.status.msg` says what it asks (for example `approve Bash: touch hello.txt`, or `answer: Pick red or blue. (Red · Blue)`).

- A **tool permission** prompt (`kind` is `permission`) names a command or file and asks `Do you want to ...?`.
- A **question prompt** (`kind` is `question`) has options and no command or file request.

Read the output too: the keys depend on the menu.

## Read recent output

```sh
hc read <address> --lines 40 | grep -v '^[[:space:]]*$' | tail -n 40
```

`hc read` prints the whole screen and the history above it, with many empty lines; the filter keeps the last 40 lines with text.

## Send text or keys to a live Worker

- Answer an Input Request. Read the menu first: the keys depend on whether its options have numbers.
  - **Numbered menu:** send the digit of the option. The digit selects at once; send no `enter`.
    - one-shot approve: `hc keys <address> 1`
    - deny: read the menu and send the digit of the option whose text is `No`. Do not use a fixed digit: the number of options changes. Example, a Claude Code permission prompt: `1. Yes`, `2. Yes, and always allow ...`, `3. Yes, and switch to auto mode`, `4. No`; here deny is `4`, and `3` approves.
  - **Menu with no numbers:** move the `❯` cursor with `down` or `up`, then press `enter`, in one command. Example, from the first option to the second: `hc keys <address> down enter`.
    - trust the Workspace folder (the folder-trust prompt at start; the cursor starts on `No, exit`): `hc keys <address> down enter`. The Workspace is the Worker's own worktree, so always trust it. Then check that the first prompt landed (step 3 of "Spawn a Worker"): the agent often drops it at this step.
  - Never send a digit before you read the menu. Never choose an option that says `always allow` or `don't ask again` (in Claude Code usually `2`): it stores a permanent permission rule. Never choose `Yes, and switch to auto mode`: it changes the Worker's permission mode. Never choose any other option that approves for the rest of the session. Never choose `No, exit` on the folder-trust prompt: it ends the Worker. Never send `y` or `n` (the menu ignores them). Never send `esc`: it destroys the prompt.
- Send a prompt (for example the gap-fill re-prompt): `hc send <address> "<text>"`, or for a long prompt in a file, `hc send <address> "$(cat <file>)"`. `hc send` pastes the text and presses Enter. Never use `--force`.
  - If the Worker shows an Input Request, hc refuses the prompt (exit 9, `kind` `blocked`) and types nothing: answer the Input Request first.
  - If hc says the Worker `is still starting` (exit 5), nothing was typed: wait 5 seconds and send again.
- Check that a prompt landed: the JSON of `hc send` has `"started": true`. If it has `"started": false`, read the output. If the text sits unsent in the input box, submit it with `hc keys <address> enter`.
- Wait for the next settled status (the permission-drain loop): `hc wait <address> --timeout 15`. The timeout is in seconds. It returns with `"reason": "status"` and the new `status` (`idle`, `done` or `blocked`), or with `"reason": "timeout"` when the Worker is still `working`.

## Stop a Worker

```sh
hc kill <address>
hc rm <address>
```

`hc kill` ends the agent process; `hc rm` removes the finished terminal (it stays in `hc ls --all` until then). If the Worker already exited, `hc kill` fails with `not_found` or `finished`: ignore that and run `hc rm`. The worktree and the branch stay: the Orchestrator never deletes a Workspace. Stop only `ol-` terminals that `state.json` names, never another terminal of the Owner's core.

## Codex agent

To run Codex (`codex`) Workers instead of Claude Code, change "Spawn a Worker" step 2 to:

```sh
hc run --bg --json --name ol-<slug> --cwd <workspace-path> --no-parent --outlive-parent --no-notify \
  "$(command -v codex)" --no-daemon --model {{WORKER_MODEL}} --sandbox workspace-write --ask-for-approval never \
  -c sandbox_workspace_write.network_access=true {{EXTRA_DIRS}} "$(cat <workspace>/.openloops/<slug>/first-prompt.md)"
```

- `--no-daemon` is necessary: without it, Codex runs its commands outside hc.
- Model flag: `--model <model>`. Effort: add `-c model_reasoning_effort=<level>`.
- Auto mode: `--sandbox workspace-write --ask-for-approval never`. Codex then runs commands in its sandbox and never asks for approval, so a Codex Worker rarely shows an Input Request. The sandbox can write only in the Workspace and in each `--add-dir`. `-c sandbox_workspace_write.network_access=true` lets the Worker push its branch and open the PR; with the Local branch Review System you can leave it out. Bypass mode is `--dangerously-bypass-approvals-and-sandbox`: use it only on a machine that is itself a sandbox.
- Extra directories: `{{EXTRA_DIRS}}` uses the same `--add-dir <path>` flag. For Codex, also add the project repo: a commit in a worktree writes into the project repo's `.git` directory, which is outside the sandbox.
- Build Spec prefix: none. Leave it out.
- Exploration Spec with `agent: <name>`: Codex has no agent flag. Start the first prompt with "Act as the agent in `<agents-dir>/<name>.md`." (the path of that agent's instructions file).
- Start prompts: in a new folder, Codex shows `Trust this folder?` (`› 1. Trust and continue`; the digit does not select here: press `hc keys <address> enter`), and it can show `Hooks need review` (choose `Continue without trusting (hooks won't run)`: `hc keys <address> down down enter`). Codex drops the first prompt after these prompts: when the input box is empty at turn 0, send the first prompt again as "Send a prompt" says.
- Status: hc reports `working`, `idle`, `done` and `blocked` for Codex too; the table above is the same.
- Input Request: read the menu and choose the option that approves this one time; never choose an option that approves for the rest of the session or always.
