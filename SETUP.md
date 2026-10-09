# Set up Open Loops

These are instructions for the Owner's coding agent. The Owner says "Set up Open Loops from <repo URL>", and you follow the steps below in order. The words in this file (Task, Slot, Cycle, Worker, Workspace, and so on) are defined in [`GLOSSARY.md`](GLOSSARY.md).

At the end, the Open Loops home directory has the five notes files, the third-party skills are installed, the Host starts a Cycle on a schedule, and a sample Task has reached In Review.

## Rules for the setup agent

- **Find out before you ask.** Never ask the Owner something that a command can tell you (step 1).
- **One question at a time.** Each question has a recommended default, written first. The Owner can answer "yes" to take it.
- **Report gaps.** For each Slot, check the chosen tool against the Slot's Contract and say what it is missing, with a way to fix the gap or another tool to pick.
- **Real values go to the home directory only.** Write IDs, paths, repo names and logins into the notes files in the home directory. Never write them into the Open Loops repo: the files in the repo hold placeholders only.
- **A re-run changes only what the Owner asks** (see "Re-run setup").
- **Ask before each change outside the home directory**: the crontab, a Host's scheduled job, labels in a Tracker, an issue for the sample Task.

## 0. Get the repo

If you are not in a clone of the Open Loops repo, clone it. Recommended place: `~/.openloops/open-loops`.

```sh
git clone <repo URL> ~/.openloops/open-loops
```

In the steps below, `<clone>` is the clone, `<core>` is `<clone>/core` (the notes files call it `{{CORE_DIR}}`), and `<home>` is the Open Loops home directory (default `~/.openloops/`; the notes files call it `{{HOME_DIR}}`).

## 1. Explore

Check these without questions. Record what you find.

| Check | How |
|---|---|
| Agent CLIs | `command -v claude codex` |
| Slot CLIs | `command -v git gh herdr tmux timeout crontab python3 npx` |
| GitHub login | `gh auth status` |
| MCP servers | `claude mcp list`; for Codex, the `[mcp_servers]` tables in `~/.codex/config.toml` |
| Are you a Host? | Are you a KiroCrew or OpenClaw agent, or did the Owner say "You are the Host"? Then that product is the Host. |
| Existing setup | The notes files `<home>/{tracker,host,runtime,notifier,review}.md`, `<home>/state.json`, and a crontab line with "Run one Open Loops Cycle" (`crontab -l`) |
| Runtime server | `tmux ls` (a tmux server runs), `herdr agent list` (a Herdr server answers) |
| Project repo | The git repo in the current directory, if any: its path, its `origin` remote (a GitHub repo?), its default branch, and hints for the build and test command (`Makefile`, `package.json` scripts, `pyproject.toml`, `Cargo.toml`, a CI file) |

If the notes files exist, this is a re-run: go to "Re-run setup".

## 2. Present the findings

Show the Owner a short table: each finding, and what it means for each Slot (for example "`gh` is logged in: the GitHub Issues Tracker and the GitHub PR Review System can work"). Then start the questions.

## 3. Choose a tool for each Slot

Ask about the Slots in this order, one at a time. For each Slot:

1. Recommend a tool: the default, or the fallback if the default cannot work on this machine (step 1 tells you). Name the other examples.
2. When the Owner picks a tool, read the Contract in `<clone>/adapters/<slot>/README.md` and its Contract map for that example. Check each capability on this machine. Report each gap, with a fix or another tool. A tool with no example notes file is allowed: then write its notes file with the Owner, one Contract item at a time.
3. Collect the values for the `{{...}}` placeholders of that example notes file.

| Slot | Default | Fallback and other examples | Placeholders to fill |
|---|---|---|---|
| Tracker | GitHub Issues: [`tracker/github-issues.md`](adapters/tracker/github-issues.md) | Markdown files (no account): [`tracker/markdown.md`](adapters/tracker/markdown.md) | GitHub Issues: `{{TRACKER_OWNER}}/{{TRACKER_REPO}}` (the repo that holds the Tasks; it can differ from the project repo). Markdown: `{{TRACKER_DIR}}` (default `<home>/tasks`; make the directory). |
| Host | cron + `claude -p`: [`host/cron-claude.md`](adapters/host/cron-claude.md) | cron + `codex exec`: [`host/cron-codex.md`](adapters/host/cron-codex.md); [KiroCrew](adapters/host/kirocrew.md); [OpenClaw](adapters/host/openclaw.md) | `{{HOME_DIR}}`, `{{CORE_DIR}}`, `{{ORCHESTRATOR_MODEL}}`, `{{ORCHESTRATOR_EFFORT}}` (where the example has it), the permission mode (`{{PERMISSION_MODE}}` or `{{CODEX_PERMISSION_FLAGS}}`), and the interval (default 30 minutes). With the wiki module (step 5): `{{GARDENER_DIR}}` and `{{WIKI_DIR}}`. |
| Runtime | Herdr (recommended, if `herdr` is installed): [`runtime/herdr.md`](adapters/runtime/herdr.md) | tmux: [`runtime/tmux.md`](adapters/runtime/tmux.md) | `{{WORKER_MODEL}}`, `{{PERMISSION_MODE}}`, `{{HOME_DIR}}`, `{{EXTRA_DIRS}}` (one `--add-dir <path>` for the home directory, the Markdown Task directory if any, and each directory that holds Specs). The agent: Claude Code or Codex (each example has a "Codex agent" section). The cap on live Workers (default 5). |
| Notifier | The log file: [`notifier/log-file.md`](adapters/notifier/log-file.md) | The Host's own messaging (KiroCrew, OpenClaw) or a messaging MCP server: see [`notifier/README.md`](adapters/notifier/README.md) | `{{NOTIFIER_LOG}}` (default `<home>/notifications.log`). |
| Review System | GitHub PR (if the project's `origin` is on GitHub and `gh` is logged in): [`review/github-pr.md`](adapters/review/github-pr.md) | Local branch (no hosting service): [`review/local-branch.md`](adapters/review/local-branch.md) | From step 4: `{{PROJECT_REPO}}`, `{{BUILD_TEST_COMMAND}}`, and for GitHub PR `{{OWNER}}/{{REPO}}`. "Open PRs as": draft (default) or ready. "Review rounds": new commits (default) or amend (for a review tool that takes an amended commit as a new revision). |

Notes for each Slot:

- **Tracker, GitHub Issues:** the Tracker needs four state labels. With the Owner's yes, create them with the command in `tracker/github-issues.md` ("The Owner creates the four labels once").
- **Host:** if you are a KiroCrew or OpenClaw agent, recommend your own product as the Host. A Host must run on a machine that is on when the Owner is away (a remote machine or an always-on local machine). The Host, the Runtime and the Workspaces are on one machine.
- **Host and Runtime, permission mode.** Ask for the permission mode of the Orchestrator (Host) and of the Workers (Runtime) together, and show this warning first:

  > **Warning: unattended agents.** The Orchestrator and the Workers run with nobody watching, so they must never wait on a permission prompt. That needs auto mode (an agent-side check of each action, for example Claude Code `--permission-mode auto`, or Codex `--sandbox workspace-write --ask-for-approval never`) or bypass mode (no checks at all). On KiroCrew (`--approval-mode auto`) and OpenClaw (the `yolo` preset), the only unattended mode approves every tool with no check: it is bypass mode under another name. Setup uses it on those Hosts, and says so to the Owner. In both modes an agent can run commands, change files and use your logins (`gh`, MCP servers) without asking you. A wrong or hostile Spec, Task comment or web page can make it do harm. Recommended: auto mode, on a machine or account that holds only what Open Loops needs. Use bypass mode only on a machine that is itself a sandbox. You can stop everything at any time (see "Stop and remove").

  Settle the permissions with the Owner: auto or bypass mode, and any allow rules the Owner wants for their agent. Do not prescribe an allowlist.
- **Runtime:** the Runtime server (tmux or Herdr) must run before a Cycle starts, and the Owner starts it from their own shell, never you: a server that an agent's shell starts passes that agent's sandbox to every Worker. Tell the Owner how (`tmux new-session -d -s main`, or open `herdr` once).
- **Models:** `host.md` names the Orchestrator's model and effort, `runtime.md` the Workers'. Ask for each: `default` (recommended: the agent's own default model, which follows its upgrades) or a model name. Write `default` or the name in the notes file. With `default`, leave `--model` and its value out of the start commands that you write: the crontab line or the Host's scheduled job (`host.md`), and the Worker start commands (`runtime.md`). The Owner controls cost and quality here.

## 4. Ask about the project

Ask one at a time:

1. **Project repo**: the absolute path of the repo the Workers work in. Default: the repo found in step 1.
2. **Build and test command**: the one command a Worker runs before each PR. Propose the command that you found in step 1 (for example `make test` or `npm test`), and say where you found it.
3. **Follow-up prefix**: the prefix that marks a Follow-up comment on a Task. Default `ACTION:`.

For more than one project, repeat questions 1 and 2. Each project is one row in the "Projects" table of `review.md`.

## 5. Optional modules

Ask one yes/no question for each optional module, default "no". A "no" installs nothing. A "yes" follows that module's setup steps, written under its question. Do those steps after step 7: they use the skills that step 7 installs.

In these steps, `<skills dir>` is the agent's own skills directory: `~/.claude/skills` for Claude Code, and `~/.agents/skills` (the shared copy) for Codex and other agents. If the Owner uses both, do each step for both. `<npx agents>` is the agent ids of step 7 (`OPENLOOPS_NPX_AGENTS`, default `codex`). If `OPENLOOPS_SKIP_THIRD_PARTY=1`, skip the `npx skills add` installs here too, and tell the Owner which skill to install another way.

<!-- Each optional module adds its own subsection here: "### <module>", the yes/no question with its default, and the steps for a "yes". -->

### capture

**Question:** "Do you want the capture module? Your agent keeps each idea in its own raw idea file, appends the grill transcript to it, and turns it into a self-contained Spec. (yes/no, default no)"

On "yes":

1. Ask where the raw idea files go: `{{IDEAS_DIR}}`, default `<home>/ideas`. Then ask where the finished Specs go: `{{SPECS_DIR}}`, default `<home>/specs`. Make both directories.
2. The Workers must read the Specs. If `{{SPECS_DIR}}` is not under a directory of `{{EXTRA_DIRS}}` in `runtime.md`, add an `--add-dir` for it.
3. Copy [`modules/capture/capture.md`](modules/capture/capture.md) to `<home>/capture.md` and replace its two placeholders.
4. With the Owner's yes, link it from the agent's own instructions file, only if no link to it is there yet:
   - **Claude Code:** add the line `@<home>/capture.md` to `~/.claude/CLAUDE.md`.
   - **Codex:** add the text of `<home>/capture.md` to `~/.codex/AGENTS.md`, between the lines `<!-- open-loops capture:start -->` and `<!-- open-loops capture:end -->` (a re-run replaces the text between them).
5. Install the `wayfinder` skill from [mattpocock/skills](https://github.com/mattpocock/skills), which the rules name. Claude Code: the `mattpocock-skills` plugin of step 7 holds it. Other agents: `npx skills add mattpocock/skills --skill wayfinder -g -y --agent <npx agents>`. If the install fails, tell the Owner and go on.

### refine

**Question:** "Do you want the refine module? It adds two skills, `spec-task` and `spec-exploration`, that interview you until an idea is a Build Spec or an Exploration Spec that a Worker can run without you. (yes/no, default no)"

On "yes":

1. Copy the folders [`modules/refine/skills/spec-task`](modules/refine/skills/spec-task) and [`modules/refine/skills/spec-exploration`](modules/refine/skills/spec-exploration) into `<skills dir>`. If a folder with the same name is already there and differs, ask the Owner before you replace it.
2. In the two copied `SKILL.md` files, replace `{{CORE_DIR}}` with `<core>`. Check: `grep -rn '{{' <skills dir>/spec-task <skills dir>/spec-exploration` prints nothing.
3. Install the `domain-modeling` skill from [mattpocock/skills](https://github.com/mattpocock/skills): the two skills use its glossary and ADR formats. Claude Code: the `mattpocock-skills` plugin of step 7 holds it. Other agents: `npx skills add mattpocock/skills --skill domain-modeling -g -y --agent <npx agents>`. If the install fails, tell the Owner and go on.

### wiki

**Question:** "Do you want the wiki module? A central LLM wiki for your Specs, decisions, glossary terms and results, shared by all your projects. Open Loops works without it; with it, a Task's `Spec:` line can point to a Spec page in the wiki. (yes/no, default no)" Details: [`modules/wiki/README.md`](modules/wiki/README.md).

On "yes":

1. **Wiki directory.** Ask for its absolute path. Default `~/llm-wiki`. Do not put it in `<home>`: removal deletes `<home>`, and the wiki holds the Owner's knowledge. If the directory already has an `AGENTS.md` or `agents.md`, it is an existing wiki: use it as it is and go to step 4.
2. **Make the wiki.** Copy the scaffold without overwriting a file, add the two Spec templates, and make the first directories:

   ```sh
   mkdir -p <wiki>
   cp -Rn <clone>/modules/wiki/scaffold/. <wiki>/ || true
   cp -n <core>/templates/build-spec.md <core>/templates/exploration-spec.md <wiki>/wiki/.templates/ || true
   mkdir -p <wiki>/raw <wiki>/wiki/projects/hubs <wiki>/wiki/projects/sources
   [ -d <wiki>/.git ] || git -C <wiki> init -q
   ```

   `cp -n` never overwrites a file; some `cp` versions exit non-zero when they skip one, so `|| true` keeps going. Append an `init` entry to `<wiki>/wiki/log.md` in the format of `AGENTS.md` §8. Show the Owner the example wiki in `<clone>/modules/wiki/example/`; do not copy it.
3. **Search (optional).** Tell the Owner that qmd gives fast wiki search and is optional: without it, the agents search with `grep`. To add it later, the Owner follows "Search" in `modules/wiki/README.md`.
4. **Let the Workers read the wiki.** If `<wiki>` is not under a directory of `{{EXTRA_DIRS}}` in `<home>/runtime.md`, add an `--add-dir <wiki>` for it.
   If the Owner said yes to capture, recommend `<wiki>/raw/ideas` for `{{IDEAS_DIR}}` and `<wiki>/wiki/projects/sources` for `{{SPECS_DIR}}`, where the manual keeps them; with the Owner's yes, change them in `<home>/capture.md`.
5. **Tell the Owner the `Spec:` rule.** A Task's `Spec:` line may point to a wiki page: `Spec: <wiki>/wiki/projects/sources/<name>.md`, made from `<wiki>/wiki/.templates/build-spec.md` or `exploration-spec.md`. Without a `Spec:` line, the Task body is the Spec, as before. An agent session in `<wiki>` follows `<wiki>/AGENTS.md` (Claude Code reads it through `<wiki>/CLAUDE.md`).
6. **wiki-gardener.** Keep the "Second job: wiki-gardener" section of the chosen Host example in `<home>/host.md` (step 6 fills `{{GARDENER_DIR}}` = `<clone>/modules/wiki/gardener` and `{{WIKI_DIR}}` = `<wiki>`; step 8 starts the job, default once a day). Tell the Owner how to apply a proposal: "wiki-gardener" in `modules/wiki/README.md`.

## 6. Write the notes files

1. Make the home directory: `mkdir -p <home>`.
2. For each Slot, copy the chosen example to its notes file name in the home directory, then replace each `{{...}}` placeholder with the value from steps 3, 4 and 5:

   | Notes file | From |
   |---|---|
   | `<home>/tracker.md` | the chosen `adapters/tracker/*.md` |
   | `<home>/host.md` | the chosen `adapters/host/*.md` |
   | `<home>/runtime.md` | the chosen `adapters/runtime/*.md` |
   | `<home>/notifier.md` | the chosen `adapters/notifier/*.md` |
   | `<home>/review.md` | the chosen `adapters/review/*.md` |

3. Edit the copies for the Owner's answers that are not placeholders: a Follow-up prefix other than `ACTION:` (in `tracker.md`; it is the same prefix everywhere), an interval other than 30 minutes (in `host.md`: the cron schedule, the "Interval" line, and the `timeout`, which stays the interval minus 5 minutes), `ready` instead of `draft` or `amend` instead of `new commits` (in `review.md`), a cap other than 5 (in `runtime.md`), the "Codex agent" command if the Workers run Codex. Without the wiki module, delete the "Second job: wiki-gardener" section and its line in "How to stop and remove" from `host.md`.
4. Check that no placeholder is left: `grep -n '{{' <home>/*.md` prints nothing.
5. Install the core agents where the Workers find them: `mkdir -p <home>/.claude/agents && cp <core>/agents/*.md <home>/.claude/agents/`.

Do not make `state.json`: the first Cycle makes it.

## 7. Install the third-party skills

The core uses skills from other projects. They are never copied into the Open Loops repo. The installer gets them from their upstream source, with one route for each agent: the Claude Code plugin marketplace for Claude Code (a plugin is installed whole, so it can bring more skills than the core uses), and `npx skills add` with an explicit skill list for Codex and other agents.

```sh
<clone>/install-third-party.sh
```

- It is safe to run again: a skill that is already installed is skipped.
- A failed install prints one `warn:` line, and the installer goes on. Tell the Owner each `warn:` line: the Worker rules need those skills.
- Set `OPENLOOPS_SKIP_THIRD_PARTY=1` to skip all third-party installs (offline or locked-down machines). Then the Owner installs the skills another way.
- Set `OPENLOOPS_NPX_AGENTS` to the agent ids of the `npx skills` route (default `codex`, if `codex` is on PATH), for example `OPENLOOPS_NPX_AGENTS="codex cursor"`.

What it installs, and the credits (made from [`third-party.json`](third-party.json); `./install-third-party.sh --check` keeps this table, [`NOTICE`](NOTICE) and the data file the same):

<!-- credits:start -->
| Source | Author | License | How Open Loops uses it |
|---|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock | MIT | The default review skill `code-review` in the Worker's completion steps. Optional modules: the refine skills `spec-task` and `spec-exploration` are derived in part from its skills (MIT, attribution in each `SKILL.md`) and use its `domain-modeling`; the capture rules name its `wayfinder`. Installed by setup from upstream. |
| [obra/superpowers](https://github.com/obra/superpowers) | Jesse Vincent | MIT | The Worker rules use `verification-before-completion`, `systematic-debugging`, `receiving-code-review` and `subagent-driven-development`. Installed by setup from upstream. |
| [herdrdev/herdr](https://github.com/herdrdev/herdr) | The Herdr authors | Apache-2.0 | The recommended Runtime. The Owner installs the `herdr` program from its own docs. Not installed by setup. |
| [tobi/qmd](https://github.com/tobi/qmd) | Tobi Lutke | MIT | Optional local search for the wiki module. The Owner installs the `qmd` program from its own docs. Not installed by setup. |
<!-- credits:end -->

These are separate projects with their own licenses. They are downloaded to the Owner's machine when setup runs. They are not part of this repository.

## 8. Start the Host

> **Warning:** from this step on, agents run unattended in the permission mode from step 3 (see the warning there). Start the Host only after the Owner says yes.

1. Make sure that the Runtime server runs (step 1: `tmux ls` or `herdr agent list`). If not, ask the Owner to start it from their own shell.
2. Start the Host as `<home>/host.md` says in "How a Cycle starts":
   - **cron + `claude -p` or `codex exec`:** add the crontab line from `host.md`, with the `PATH=` line above it, only if no line with "Run one Open Loops Cycle" for this home directory is already there: `(crontab -l 2>/dev/null; cat <file with the two lines>) | crontab -`. Show the Owner `crontab -l` after.
   - **KiroCrew or OpenClaw:** create your own scheduled job with the command in `host.md`, and write its id into `host.md` ("How to stop and remove" uses it).
   - **wiki-gardener** (only if `host.md` has "Second job: wiki-gardener"): start that job in the same way, only if no job with "Run the wiki gardener" for this home directory is already there.

## 9. Verify with the sample Task

The sample Build Task asks a Worker to add `hello.txt` to the project repo on the branch `ol-hello-file`. Use it to see one Task reach In Review.

1. Write the sample Build Spec: copy [`examples/specs/hello-file.md`](examples/specs/hello-file.md) to `<home>/specs/hello-file.md`, replace `{{PROJECT_REPO}}` with the project repo, and set `branch:` to the project's default branch if it is not `main`. `<home>` is already in `{{EXTRA_DIRS}}`, so the Worker can read it.
2. Make the sample Task in the Tracker:
   - **Markdown:** copy [`examples/tasks/hello-file.md`](examples/tasks/hello-file.md) to `<Task directory>/hello-file.md`, and replace `{{SPEC_DIR}}` with `<home>/specs`.
   - **GitHub Issues:** with the Owner's yes, make an issue with the title and the body of that file (the text between the frontmatter and `## Comments`, with `{{SPEC_DIR}}` replaced), and the label `ol:ready`. Then set `tracker_id:` in the Spec to the issue number.
3. Wait for the next Cycle, or, with the Owner's yes, run the Cycle command from `host.md` once now. Watch the Notifier for `spawned`, then `in_review`; `<home>/orchestrator.log` has one entry for each Cycle.
4. Done when: the Task is In Review, the branch `ol-hello-file` has a commit with `hello.txt`, and the Task has a comment that names the PR (GitHub PR) or the branch (Local branch).
5. Tell the Owner how to clean up: close the sample PR (or delete the branch `ol-hello-file`), then move the Task to Done. The Workspace stays under `<project repo>/.openloops/`.

If the Task does not reach In Review, read `<home>/orchestrator.log`, `<home>/host.log` and the Notifier, and fix the notes file of the Slot that failed.

## Re-run setup

When the notes files exist:

1. Read them all, and show the Owner the current tool and values for each Slot and project.
2. Ask what to change. Change only that: edit only the lines of that notes file (or the Slot's whole file, if the Owner picks another tool for it). Keep every other file and line as it is. Never touch `state.json` or the Workspaces.
3. Do only the steps that the change needs: for example step 7 if a new agent needs the skills, the module's steps of step 5 if the Owner turns a module on, step 8 if the interval or the Host changed (replace the old crontab line or scheduled job; never leave two).

## Stop and remove

Follow "How to stop and remove" in `<home>/host.md`. In short: stop the schedule first (the crontab line, or the Host's scheduled job), then stop the live `ol-` Workers with the Runtime. To remove Open Loops fully, then delete the home directory if the Owner no longer needs its state and logs. If the clone is in the home directory (the default `~/.openloops/open-loops`), that deletes the clone too.

The Workspaces under each project's `.openloops/` and the `ol-` branches are kept: they hold the Owner's work. The third-party skills stay installed; remove them with their own tools (`claude plugin uninstall <plugin>`, `npx skills remove <skill>`) if the Owner wants.
