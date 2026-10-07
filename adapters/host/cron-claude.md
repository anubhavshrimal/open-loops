# host.md: cron + `claude -p` Host

Example notes file for the Host Slot. Copy it to `<home>/host.md` and replace each `{{...}}` placeholder.

Host name: cron + `claude -p` (Claude Code in print mode, started by the system cron)

Home directory: `{{HOME_DIR}}`

Interval: 30 minutes

Orchestrator model: `{{ORCHESTRATOR_MODEL}}` (add `--effort <level>` to the command to set the effort)

Permission mode: `{{PERMISSION_MODE}}` (the Orchestrator runs unattended, so it must never wait on a permission prompt)

## How a Cycle starts

Tools: `claude -p` has a shell and the Owner's configured MCP servers, so the Orchestrator can use the tools that the other notes files name.

Each Cycle is a new `claude -p` session that reads the core Orchestrator prompt. `timeout` ends a hung Cycle 5 minutes before the next one starts, so Cycles cannot pile up:

```sh
cd {{HOME_DIR}} && timeout 25m claude -p "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." --model {{ORCHESTRATOR_MODEL}} --permission-mode {{PERMISSION_MODE}} >> {{HOME_DIR}}/host.log 2>&1
```

Crontab line (`crontab -e`; cron has a short `PATH`, so set it to include `claude`, `git` and the Runtime's CLI, `herdr` or `tmux`):

```
PATH=/usr/local/bin:/usr/bin:/bin
*/30 * * * * cd {{HOME_DIR}} && timeout 25m claude -p "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." --model {{ORCHESTRATOR_MODEL}} --permission-mode {{PERMISSION_MODE}} >> {{HOME_DIR}}/host.log 2>&1
```

If you change the interval, change the `timeout` to the interval minus 5 minutes.

## How to stop and remove

- Pause: comment out the crontab line (`crontab -e`). Live Workers keep running until you stop them with the Runtime.
- Remove: delete the crontab line, stop the `ol-` Workers with the Runtime, then delete the home directory if you no longer need its state and logs. The Workspaces under `<repo>/.openloops/` are kept.
