# host.md: cron + `codex exec` Host

Example notes file for the Host Slot. Copy it to `<home>/host.md` and replace each `{{...}}` placeholder.

Host name: cron + `codex exec` (Codex in non-interactive mode, started by the system cron)

Home directory: `{{HOME_DIR}}`

Interval: 30 minutes

Orchestrator model: `{{ORCHESTRATOR_MODEL}}`, effort `{{ORCHESTRATOR_EFFORT}}` (`-c model_reasoning_effort=...` in the command)

Permission mode: `{{CODEX_PERMISSION_FLAGS}}`. `codex exec` never asks for approval. Pick the sandbox:

- auto mode: `--sandbox workspace-write -c sandbox_workspace_write.network_access=true` plus one `--add-dir <path>` for each directory that the Orchestrator writes outside the home directory (the Tracker files, each project repo). Network access lets the Slot tools reach their services. The sandbox can also block the Runtime's socket (Herdr or tmux); if a Runtime command fails with a permission error, add the socket's directory with `--add-dir`, or use bypass mode.
- bypass mode: `--dangerously-bypass-approvals-and-sandbox`. Use it only on a machine that is itself a sandbox.

## How a Cycle starts

Tools: `codex exec` has a shell and the MCP servers in the Owner's Codex configuration, so the Orchestrator can use the tools that the other notes files name.

Each Cycle is a new `codex exec` session that reads the core Orchestrator prompt. `timeout` ends a hung Cycle 5 minutes before the next one starts, so Cycles cannot pile up:

```sh
cd {{HOME_DIR}} && timeout 25m codex exec --cd {{HOME_DIR}} --skip-git-repo-check --model {{ORCHESTRATOR_MODEL}} -c model_reasoning_effort={{ORCHESTRATOR_EFFORT}} {{CODEX_PERMISSION_FLAGS}} "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." >> {{HOME_DIR}}/host.log 2>&1
```

`--skip-git-repo-check` is needed because the home directory is not a git repo.

Crontab line (`crontab -e`; cron has a short `PATH`, so set it to include `codex`, `git` and the Runtime's CLI):

```
PATH=/usr/local/bin:/usr/bin:/bin
*/30 * * * * cd {{HOME_DIR}} && timeout 25m codex exec --cd {{HOME_DIR}} --skip-git-repo-check --model {{ORCHESTRATOR_MODEL}} -c model_reasoning_effort={{ORCHESTRATOR_EFFORT}} {{CODEX_PERMISSION_FLAGS}} "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." >> {{HOME_DIR}}/host.log 2>&1
```

If you change the interval, change the `timeout` to the interval minus 5 minutes.

## Second job: wiki-gardener

Add this job only if the Owner said yes to the wiki module. It is a second scheduled job, next to the Cycle job: it runs the wiki gardener lint prompt once a day (default), proposes fixes where the wiki drifts from the Tracker and the docs, and sends one Notifier message. It never edits the wiki. `{{GARDENER_DIR}}` is `modules/wiki/gardener` in the Open Loops clone, and `{{WIKI_DIR}}` is the wiki directory. The Owner applies the approved items later in an agent session that follows `{{GARDENER_DIR}}/apply.md` (see `modules/wiki/README.md`).

Crontab line (the same `PATH` line as the Cycle job covers it). `timeout 60m` ends a hung run. The lint run writes only in the home directory, so the auto-mode sandbox needs no extra `--add-dir` for it:

```
0 6 * * * cd {{HOME_DIR}} && timeout 60m codex exec --cd {{HOME_DIR}} --skip-git-repo-check --model {{ORCHESTRATOR_MODEL}} -c model_reasoning_effort={{ORCHESTRATOR_EFFORT}} {{CODEX_PERMISSION_FLAGS}} "Run the wiki gardener. Follow {{GARDENER_DIR}}/lint.md. Wiki: {{WIKI_DIR}}. Home directory: {{HOME_DIR}}." >> {{HOME_DIR}}/wiki-gardener.log 2>&1
```

## How to stop and remove

- Pause: comment out the crontab line (`crontab -e`). Live Workers keep running until you stop them with the Runtime.
- Remove: delete the crontab line, stop the `ol-` Workers with the Runtime, then delete the home directory if you no longer need its state and logs. The Workspaces under `<repo>/.openloops/` are kept.
- wiki-gardener job: pause or remove its crontab line in the same way.
