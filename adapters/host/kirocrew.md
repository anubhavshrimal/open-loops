# host.md: KiroCrew Host

Example notes file for the Host Slot. Copy it to `<home>/host.md` and replace each `{{...}}` placeholder.

Host name: KiroCrew (https://github.com/kirodotdev/KiroCrew), a persistent agent workspace that runs on the Owner's machine and has scheduled jobs.

Setup: give the KiroCrew agent the repo link, for example in its chat: "Set up Open Loops from <repo URL>. You are the Host." The agent follows `SETUP.md`, writes the notes files into the home directory, and creates its own scheduled job (see "How a Cycle starts").

Home directory: `{{HOME_DIR}}` (the Open Loops home directory, default `~/.openloops/`; it is separate from KiroCrew's own home directory)

Interval: 30 minutes

Orchestrator model: `{{ORCHESTRATOR_MODEL}}` (the job's `--model` option), effort `{{ORCHESTRATOR_EFFORT}}` (KiroCrew's `agent.reasoning_effort` setting, or the agent spec of a job agent named with `--agent <name>`)

Permission mode: auto (`--approval-mode auto`: KiroCrew approves every tool with no prompt and no check, which is the same as bypass mode; `auto` is the only value that `--approval-mode` takes). KiroCrew's security docs name the risk of an unbounded auto-approve window; read them before you turn it on.

## How a Cycle starts

Tools: a KiroCrew agent has a shell, file and web tools, and the MCP servers in its agent spec, so the Orchestrator can use the tools that the other notes files name.

One scheduled job runs one Cycle every 30 minutes. Each run must be a new session (`--no-persistent-session`), so that no chat memory carries over between Cycles: `state.json` is the only truth.

```sh
kirocrew cron add "open-loops-cycle" "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}." --every 1800 --timeout-secs 1500 --model {{ORCHESTRATOR_MODEL}} --no-persistent-session --approval-mode auto
```

- When the agent creates the job from chat, it uses its own scheduling tool with the same values (every 1800 seconds, a budget of 1500 seconds, the model, a fresh session for each run, approval mode auto).
- Timeout: `--timeout-secs 1500` ends a hung Cycle after 25 minutes (the interval minus 5 minutes), so Cycles cannot pile up. If you change the interval, change the timeout too.
- Notifier: the job output goes to the Owner's KiroCrew chat by default. To use that chat as the Notifier, write a `notifier.md` that names the agent's send-message tool.

## Second job: wiki-gardener

Add this job only if the Owner said yes to the wiki module. It is a second scheduled job, next to the Cycle job: it runs the wiki gardener lint prompt once a day (default), proposes fixes where the wiki drifts from the Tracker and the docs, and sends one Notifier message. It never edits the wiki. `{{GARDENER_DIR}}` is `modules/wiki/gardener` in the Open Loops clone, and `{{WIKI_DIR}}` is the wiki directory. The Owner applies the approved items later in an agent session that follows `{{GARDENER_DIR}}/apply.md` (see `modules/wiki/README.md`).

One more scheduled job, once a day, each run a new session. `--timeout-secs 3600` ends a hung run after 60 minutes:

```sh
kirocrew cron add "open-loops-wiki-gardener" "Run the wiki gardener. Follow {{GARDENER_DIR}}/lint.md. Wiki: {{WIKI_DIR}}. Home directory: {{HOME_DIR}}." --every 86400 --timeout-secs 3600 --model {{ORCHESTRATOR_MODEL}} --no-persistent-session --approval-mode auto
```

To apply, the Owner pastes the text from "Copy decisions" into the KiroCrew chat with: "Follow {{GARDENER_DIR}}/apply.md."

## How to stop and remove

- Pause: `kirocrew cron pause <id>` (`kirocrew cron list` shows the id). Resume with `kirocrew cron resume <id>`. Live Workers keep running until you stop them with the Runtime.
- Remove: `kirocrew cron remove <id>`, stop the `ol-` Workers with the Runtime, then delete the home directory if you no longer need its state and logs. The Workspaces under `<repo>/.openloops/` are kept.
- wiki-gardener job: pause or remove the `open-loops-wiki-gardener` job in the same way.
