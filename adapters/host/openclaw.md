# host.md: OpenClaw Host

Example notes file for the Host Slot. Copy it to `<home>/host.md` and replace each `{{...}}` placeholder.

Host name: OpenClaw (https://github.com/openclaw/openclaw), a personal AI assistant that runs on the Owner's machine through a local Gateway and has scheduled jobs (automations).

Setup: give the OpenClaw agent the repo link, for example in its chat: "Set up Open Loops from <repo URL>. You are the Host." The agent follows `SETUP.md`, writes the notes files into the home directory, and creates its own scheduled job (see "How a Cycle starts").

Home directory: `{{HOME_DIR}}` (the Open Loops home directory, default `~/.openloops/`; it is separate from OpenClaw's own workspace)

Interval: 30 minutes

Orchestrator model: `{{ORCHESTRATOR_MODEL}}`, effort `{{ORCHESTRATOR_EFFORT}}` (the job's `--model` and `--thinking` options)

Permission mode: never prompt. OpenClaw's preset is `openclaw exec-policy preset yolo`. A scheduled job then runs unattended with the agent's full tool policy, including shell commands on the host; OpenClaw's docs say to treat it as unattended code execution.

## How a Cycle starts

Tools: an OpenClaw agent has a shell (the `exec` tool) and the MCP servers added with `openclaw mcp add`, so the Orchestrator can use the tools that the other notes files name. Make sure that the job can reach the home directory, the Tracker files and each project repo: the OpenClaw workspace is only the default working directory.

One scheduled job runs one Cycle every 30 minutes. Each run must be an isolated session (`--session isolated`), so that no chat memory carries over between Cycles: `state.json` is the only truth.

```sh
openclaw automations add --name "open-loops-cycle" --cron "*/30 * * * *" --session isolated --model {{ORCHESTRATOR_MODEL}} --thinking {{ORCHESTRATOR_EFFORT}} --message "Run one Open Loops Cycle. Follow {{CORE_DIR}}/orchestrator.md. Home directory: {{HOME_DIR}}."
```

- When the agent creates the job from chat, it uses the same values (every 30 minutes, an isolated session, the model and thinking level).
- Timeout: set the job timeout to 25 minutes (the interval minus 5 minutes; `timeoutSeconds` 1500 in the job settings), so that a hung Cycle cannot pile up. With no timeout, OpenClaw stops an isolated run after 60 minutes.
- Notifier: to use OpenClaw's own messaging as the Notifier, write a `notifier.md` that sends with `openclaw message send --channel <channel> --target <target> --message "<text>"`.

## Second job: wiki-gardener

Add this job only if the Owner said yes to the wiki module. It is a second scheduled job, next to the Cycle job: it runs the wiki gardener lint prompt once a day (default), proposes fixes where the wiki drifts from the Tracker and the docs, and sends one Notifier message. It never edits the wiki. `{{GARDENER_DIR}}` is `modules/wiki/gardener` in the Open Loops clone, and `{{WIKI_DIR}}` is the wiki directory. The Owner applies the approved items later in an agent session that follows `{{GARDENER_DIR}}/apply.md` (see `modules/wiki/README.md`).

One more automation, once a day, each run an isolated session. Set its timeout to 60 minutes (`timeoutSeconds` 3600):

```sh
openclaw automations add --name "open-loops-wiki-gardener" --cron "0 6 * * *" --session isolated --model {{ORCHESTRATOR_MODEL}} --thinking {{ORCHESTRATOR_EFFORT}} --message "Run the wiki gardener. Follow {{GARDENER_DIR}}/lint.md. Wiki: {{WIKI_DIR}}. Home directory: {{HOME_DIR}}."
```

To apply, the Owner pastes the text from "Copy decisions" into the OpenClaw chat with: "Follow {{GARDENER_DIR}}/apply.md."

## How to stop and remove

- Pause: `openclaw automations disable <id>` (`openclaw automations list` shows the id). Resume with `openclaw automations enable <id>`. Live Workers keep running until you stop them with the Runtime.
- Remove: `openclaw automations remove <id>`, stop the `ol-` Workers with the Runtime, then delete the home directory if you no longer need its state and logs. The Workspaces under `<repo>/.openloops/` are kept.
- wiki-gardener job: disable or remove the `open-loops-wiki-gardener` automation in the same way.
