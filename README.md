<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/wordmark-dark.svg">
  <img alt="Open Loops" src="assets/wordmark-light.svg" height="44">
</picture>
<img alt="Wick, the Open Loops mascot: a small lantern robot" src="assets/wick-sticker-96.png" height="48">

### Specs in, reviewed PRs out.

**Stop watching your coding agents work.** Write the next Spec while Workers build the last one. Review PRs as they arrive. And it keeps going while you sleep.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero-loop-dark.gif">
    <img src="assets/hero-loop-light.gif" width="100%" alt="An animated Tracker with illustrative Tasks, from 2 PM to 8:30 AM, compressed into 29 seconds. In the afternoon you write a Spec and move the Task to Ready; a Cycle spawns a Worker in its own git worktree; while it builds, you write the next Spec. The Worker opens a PR and moves the Task to In Review. You leave a Review comment; the next Cycle respawns the Worker in the same worktree, and a bot comment is skipped. You mark the PR ready and merge it; the next Cycle moves the Task to Done. At sunset two Workers keep going, and one Task is Gated. One of them is an Exploration Task: its Worker tries ideas through the night, keeps what works and retires the rest. At night they open PRs, and the Exploration Worker adds a results table and a findings report. In the morning you merge the PRs, the Tasks move to Done, and the Gated Task starts.">
  </picture>
</p>
<p align="center"><sub><i>An illustration of a day and a night, compressed into 29 seconds. The Tasks and PRs are illustrative, not a real run. The states, the Cycle order and the Notifier event names are the real ones.</i></sub></p>

Open Loops takes Tasks from your Tracker and gives each one to a coding-agent Worker in its own git worktree. The Worker builds, tests and reviews until the Spec's goal is met, then opens a PR. Your Review comments bring it back. You merge.

- **Nothing starts by itself.** A Worker starts only on a Task in Ready, and you put your Tasks there.
- **One git worktree per Task** (by default), on a new `ol-` branch, apart from your own checkout.
- **No agent merges.** Workers open PRs. You merge or close them.
- **Only trusted comments count.** A Review comment or Follow-up acts only if it comes from you or a user with write access. Comments from bots and other people are skipped.
- **It runs on your machine,** with your tools for each Slot. Nothing runs on a server of this project.

> [!WARNING]
> **Preview (v0.1).** The agents run unattended, with your logins. Use a machine or account that holds only what Open Loops needs, and read [Safety](#safety) first.

## Quick start

You need a machine that stays on, `git`, a coding agent with a shell and a Runtime ([Herdr](https://github.com/herdrdev/herdr) or `tmux`). The defaults also use `gh`, logged in.

1. **Install.** Tell your coding agent (Claude Code, Codex, or any agent with a shell; a KiroCrew or OpenClaw agent can be the Host itself):

   ```text
   Set up Open Loops from https://github.com/anubhavshrimal/open-loops
   ```

   The agent follows [`SETUP.md`](SETUP.md). It checks your machine and asks one question at a time, each with a default: a tool for each Slot, your project, the modules. It writes five notes files into `~/.openloops/`, installs the third-party skills, and starts the Host when you say yes.

2. **Verify.** The agent puts the sample Task [`hello-file`](examples/tasks/hello-file.md) in Ready. The next Cycle (default: every 30 minutes) spawns a Worker. The Worker adds `hello.txt` on the branch `ol-hello-file`, opens a PR and moves the Task to In Review. The Cycle after that sends `in_review`:

   ```sh
   tail ~/.openloops/notifications.log    # default Notifier: spawned, then in_review
   head ~/.openloops/orchestrator.log     # any Notifier: one entry per Cycle, newest first
   ```

3. **Your first real Task.** Write a Spec from a [template](core/templates/), make a Task that points to it, and move the Task to Ready. See [Your first real Task](docs/quickstart.md#5-your-first-real-task).

No accounts? Say "use the local fallbacks" to the agent. Then a Markdown folder is the Tracker, a local branch is the PR, and a log file is the Notifier. Step by step: [`docs/quickstart.md`](docs/quickstart.md).

## How it works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/two-loops-animated-dark.svg">
  <img alt="Two loops. The Owner moves a Task to Ready. A Cycle spawns one Worker in its own git worktree, unless the Task is Gated. The Worker runs a Closed Loop with no human: build, test, review, fix. Then the Worker opens the PR and moves the Task to In Review, and the next Cycle sends in_review. A Review comment or ACTION Follow-up from a trusted author, or a failed Check, gives a Respawn in the same worktree. Comments from bots and other users are skipped. When the Owner marks the PR ready and merges it, the next Cycle moves the Task to Done and sends done. No agent merges. A Worker that cannot go on is Blocked and asks the Owner." src="assets/two-loops-animated-light.svg" width="100%">
</picture>

1. **You write a Task** with a Spec (a Build Spec with acceptance criteria, or an Exploration Spec with a hypothesis) and move it to Ready.
2. **A Cycle starts on a schedule.** The Host (Claude Code, Codex, KiroCrew or OpenClaw) starts the Orchestrator as a new agent session; `~/.openloops/state.json` is its only memory. It spawns one Worker per Ready Task in a git worktree at `<repo>/.openloops/worktrees/<slug>`. A Task whose upstream Task is not Done is Gated: it waits for a later Cycle.
3. **The Worker runs a Closed Loop** until the Spec's goal is met: it builds, runs your build and test command, runs a review skill and fixes. Then the Worker itself commits, opens the PR, comments on the Task and moves it to In Review. The next Cycle sends `in_review`.
4. **The Open Loop continues:** a new Review comment, a failed Check or a Follow-up comment (`ACTION: ...`) gives a Respawn in the same worktree. A comment counts only from a trusted author: you, or a user with write access to the repo. A Worker that cannot go on is Blocked and asks you.
5. **You merge.** Mark the PR ready (if it is a draft) and merge it. When the PR is merged, closed, or approved by another reviewer with write access, the next Cycle moves the Task to Done and sends `done`. No agent ever merges.

The states, the Cycle and the invariants are in [`SPEC.md`](SPEC.md). The words are in [`GLOSSARY.md`](GLOSSARY.md). The reasons are in [`docs/design-decisions.md`](docs/design-decisions.md).

## Task states

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/state-map-dark.svg">
  <img alt="The Open Loop Line: the Task states as a transit map. Backlog (Owner only) leads to Ready, Working, In Review and Done. A teal Respawn loop goes from In Review back to Working in the same worktree, through a gate that only a trusted author's comment passes (you, or a user with write access); a failed Check always passes. Comments from bots and other people turn off before the gate into a dead-end spur and are skipped. A Blocked branch goes back to Ready when the blocker is cleared. Gated is a siding at Ready: a Task waits there until its upstream Task is Done. Four illustrative Tasks ride the line, each in the color of its state." src="assets/state-map-light.svg" width="100%">
</picture>

<sub>Illustrative Tasks. A train has the color of its state. No motion: still version (<a href="assets/state-map-still-light.png">light</a>, <a href="assets/state-map-still-dark.png">dark</a>). The rules are in <a href="SPEC.md">SPEC.md</a>.</sub>

## See it run

<details>
<summary><b>Watch one Task go through the whole Open Loop</b> (terminal re-enactment, about 110 seconds, captions in the clip)</summary>

<br>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/terminal-demo-dark.gif">
  <source media="(prefers-color-scheme: light)" srcset="assets/terminal-demo-light.gif">
  <img alt="Terminal re-enactment with burned-in captions. You tell your coding agent: Set up Open Loops. Setup asks one question at a time; the Host question lists Claude Code, Codex, KiroCrew and OpenClaw. The sample Task Add hello.txt goes to Ready. At 10:30 a Cycle spawns the Worker ol-hello-file in its own git worktree in a Herdr pane. The Worker builds, tests and reviews, then opens draft PR #2 itself and moves the Task to In Review. At 11:00 the next Cycle only sends in_review and writes the Cycle log. You leave a Review comment; a comment from a bot on the PR is skipped because bots are not trusted authors. At 11:30 the next Cycle respawns the Worker in the same worktree; it adds a commit, pushes and replies. You mark the draft PR ready and merge it; you do not approve your own PR. At 12:30 the next Cycle moves the Task to Done and sends done. No agent merges." src="assets/terminal-demo-light.gif" width="100%">
</picture>

<sub>A re-enactment with the default Slots (cron + <code>claude -p</code> as the Host, Herdr, GitHub Issues, a log file, GitHub PR). Task #1, PR #2 and the repo <code>you/my-app</code> are illustrative. Time is sped up; the clock shows the time of day in the story. The commands and log lines follow <a href="core/orchestrator.md"><code>core/orchestrator.md</code></a>, <a href="core/worker-rules.md"><code>core/worker-rules.md</code></a> and the <a href="adapters/"><code>adapters/</code></a> notes files; the wording follows a real <a href="tests/cycle_fixture/README.md">Cycle fixture</a> run.</sub>
</details>

## Slots

Each Slot is a place where setups differ. Its Contract (in [`adapters/`](adapters/README.md)) lists what your tool must do. A notes file in `~/.openloops/` tells the Orchestrator which tool to use and how.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/core-and-slots-dark.svg">
  <img alt="The core and its five Slots. The core is the same for every Owner: orchestrator.md (one Cycle: watches Workers, spawns and respawns them, moves Tasks, sends notices, never does Task work), worker-rules.md (every Worker: Closed Loop, then commit, test, review, open the PR, move the Task to In Review) and state.json (the only memory between Cycles). Host, host.md: starts each Cycle on a schedule; examples Claude Code, Codex, KiroCrew, OpenClaw. Runtime, runtime.md: spawns, watches and stops Workers; examples Herdr, tmux. Tracker, tracker.md: stores Tasks and their states, tells if an author is trusted; examples GitHub Issues, a Markdown folder. Review System, review.md: holds PRs, comments and Checks, tells if an author is trusted; examples GitHub PR, a local branch. Notifier, notifier.md: sends you one text message per event; examples a log file, KiroCrew or OpenClaw, an MCP server." src="assets/core-and-slots-light.svg" width="100%">
</picture>

| Slot | Does | Default | Local fallback and other examples |
|---|---|---|---|
| [Tracker](adapters/tracker/README.md) | Stores Tasks and their states | GitHub Issues via `gh` | Markdown files |
| [Host](adapters/host/README.md) | Starts a Cycle on a schedule | cron + `claude -p` (Claude Code) | cron + `codex exec` (Codex), KiroCrew, OpenClaw |
| [Runtime](adapters/runtime/README.md) | Spawns, watches and stops Workers | Herdr | tmux |
| [Notifier](adapters/notifier/README.md) | Sends you messages | log file | the Host's own messaging (KiroCrew, OpenClaw), a messaging MCP server |
| [Review System](adapters/review/README.md) | Holds PRs, Review comments and Checks | GitHub PR via `gh` | Local branch |

Your tool is not in the list? Pick it during setup. The agent checks it against the Contract, tells you what is missing, and writes its notes file with you.

## Specs

The core needs only a Tracker. A Spec is the Task body, or a file (in your project repo, `~/.openloops/specs/` or a wiki) that a `Spec:` line in the Task names. Templates: [`core/templates/`](core/templates/). Samples: [`examples/`](examples/README.md).

Three optional modules help you write Specs. Setup asks one yes/no question for each:

- [capture](modules/capture/README.md): one raw idea file per idea.
- [refine](modules/refine/README.md): interview skills that turn an idea into a Spec.
- [wiki](modules/wiki/README.md): one LLM wiki for many related projects. It holds Specs, decisions, glossary terms and results. A Task's `Spec:` line can point to a wiki page, and wiki-gardener proposes fixes when the wiki drifts.

## Safety

The Orchestrator and the Workers run with nobody watching, in auto mode (an agent-side check of each action) or bypass mode (no checks). They can run commands, change files and use your logins without asking you. A wrong or hostile Spec, Task comment or web page can make them do harm. Only a comment from a trusted author (you, or a user with write access to the repo) can start a Worker or give it an instruction; other comments, also from bots, are skipped. A Worker can still read untrusted text, for example in an issue body or on a web page. Use auto mode, on a machine or account that holds only what Open Loops needs. Use bypass mode only on a machine that is itself a sandbox.

The Host, the Runtime and the Workspaces are on one machine. Nothing runs on a server of this project.

| Slot | What runs | What it can use |
|---|---|---|
| Host | One Orchestrator agent session for each Cycle | A shell and your tools for the other Slots (for example your `gh` login and MCP servers). It reads and writes `~/.openloops/`. |
| Runtime | The Workers, each in its own worktree | A shell, the agent's own login, the Tracker tools in `tracker.md` and the Review System tools in `review.md`. |
| Tracker | Your Tracker tool | Its login (for example `gh`). The Orchestrator and the Workers both use it. |
| Review System | Your PR tool | Push rights to the remote that `review.md` names, and nothing else. No agent merges, and setup makes no repo settings. |
| Notifier | Your send tool | The send tool only. Only the Orchestrator (and wiki-gardener) sends. |

**To stop everything:** remove the schedule (`crontab -e`, or your Host's job), then stop the `ol-` Workers. See [Stop and remove](SETUP.md#stop-and-remove). Your worktrees and branches stay.

## Docs

In the order you need them:

| You want to | Read |
|---|---|
| Set up Open Loops, step by step | [`docs/quickstart.md`](docs/quickstart.md) |
| Know what your agent does during setup | [`SETUP.md`](SETUP.md) |
| Write a Spec | [`core/templates/build-spec.md`](core/templates/build-spec.md), [`core/templates/exploration-spec.md`](core/templates/exploration-spec.md), [`examples/`](examples/README.md) |
| Fix a problem | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Learn the words | [`GLOSSARY.md`](GLOSSARY.md) |
| Know the states, Contracts and invariants | [`SPEC.md`](SPEC.md) |
| Write a notes file for your own tool | [`adapters/README.md`](adapters/README.md) |
| Know why it works this way | [`docs/design-decisions.md`](docs/design-decisions.md) |
| Read the prompts | [`core/orchestrator.md`](core/orchestrator.md), [`core/worker-rules.md`](core/worker-rules.md) |
| Run the tests | [`tests/cycle_fixture/README.md`](tests/cycle_fixture/README.md) |
| Change Open Loops (people and agents) | [`AGENTS.md`](AGENTS.md) |

## Credits

Open Loops installs these projects from their upstream source. None of their files are in this repo.

<!-- credits:start -->
| Source | Author | License | How Open Loops uses it |
|---|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock | MIT | The default review skill `code-review` in the Worker's completion steps. Optional modules: the refine skills `spec-task` and `spec-exploration` are derived in part from its skills (MIT, attribution in each `SKILL.md`) and use its `domain-modeling`; the capture rules name its `wayfinder`. Installed by setup from upstream. |
| [obra/superpowers](https://github.com/obra/superpowers) | Jesse Vincent | MIT | The Worker rules use `verification-before-completion`, `systematic-debugging`, `receiving-code-review` and `subagent-driven-development`. Installed by setup from upstream. |
| [herdrdev/herdr](https://github.com/herdrdev/herdr) | The Herdr authors | Apache-2.0 | The recommended Runtime. The Owner installs the `herdr` program from its own docs. Not installed by setup. |
| [tobi/qmd](https://github.com/tobi/qmd) | Tobi Lutke | MIT | Optional local search for the wiki module. The Owner installs the `qmd` program from its own docs. Not installed by setup. |
<!-- credits:end -->

The wiki module follows Andrej Karpathy's ["LLM Wiki" pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The Exploration Worker's experiment loop follows Andrej Karpathy's [autoresearch](https://github.com/karpathy/autoresearch). The repo layout and the idea of a `SPEC.md` next to the code come from [openai/symphony](https://github.com/openai/symphony). The fonts in the images are Inter and JetBrains Mono (SIL Open Font License 1.1), drawn as outlines.

## License

[MIT](LICENSE), by Anubhav Shrimal. Third-party notices: [`NOTICE`](NOTICE).
