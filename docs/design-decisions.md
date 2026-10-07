# Design decisions

Why Open Loops works the way it does. Each entry gives the decision and the reason for it. [`SPEC.md`](../SPEC.md) states the rules; this page explains them. Open Loops started as a personal system that ran every day for months before it was made generic. Most rules below come from a problem seen in that daily use.

## The loop

**The Owner starts each Task by hand.** A Task spawns only when the Owner moves it to Ready. A finished Spec does not start by itself.
*Why:* not every Spec should run unattended. The move to Ready is the Owner's veto.

**Backlog is its own state, and the Orchestrator never reads it.**
*Why:* the Owner (alone, or with an interview agent) shapes a Task and its Spec over several sessions. A half-written Spec must be safe from pickup. Only the Owner moves a Task out of Backlog (or a refinement agent, with the Owner's yes), and only the Owner moves a Task back to Backlog.

**The Orchestrator is an agent with a prompt, not a script.**
*Why:* many of its steps are judgments: is a Worker done, blocked, or showing an Input Request; is a Follow-up already fulfilled; what context does a Respawn need. A script would need a rule for each case and would break on the first new case. An agent with a shell and the Slot tools can judge them, and the prompt keeps the mechanical parts exact.

**A new session for each Cycle; `state.json` is the only truth.**
*Why:* a long-lived session drifts. It remembers things that are no longer true, and its context grows each Cycle. A new session that reads one state file gives the same result every time, and a person can read the state file to see what the Orchestrator knows.

**The Orchestrator uses no subagents and does no Task work.**
*Why:* it must be fast and predictable. Each Cycle is a short pass over the Tracker. Task work belongs to Workers, which are separate agent processes in the Runtime, each with its own context.

**The Cycle interval lives only in `host.md`.** The prompt says "Cycle" and never a number.
*Why:* the interval is the Owner's choice of cost against speed. A number in the prompt would go stale the first time an Owner changed it.

**No special rules for overlapping Cycles, missed Cycles or pause.**
*Why:* the check for a live Worker before each spawn already stops double spawns. The crontab examples wrap each Cycle in `timeout <interval minus 5 minutes>`, so Cycles cannot pile up. To pause, the Owner stops the schedule. Each extra mechanism (a lock file, a watchdog, a pause file) would be one more thing to break and debug.

## Workers

**Workers are interactive agents in a Runtime with terminal panes (Herdr or tmux), not headless runs.**
*Why:* a headless run ends after one prompt, and it cannot show a permission or question prompt. An interactive Worker stays up: the Orchestrator can read its screen, answer a prompt, send the gap-fill prompt, and the Owner can attach and take over at any time.

**The Orchestrator is a monitor, not a restart loop.** A Worker runs as long as it needs. The Orchestrator never kills a Worker because a Cycle passed.
*Why:* an Exploration Spec can run for hours. A restart each Cycle would throw away the Worker's reasoning. The worktree keeps the code state; the live session keeps the reasoning state.

**The first prompt is short: the Worker rules path, the home directory, the Spec path, and the authorization.** The Worker reads the rest itself.
*Why:* the intelligence lives in files that are versioned and reviewed (`core/worker-rules.md` and the Spec), not in a prompt that the Orchestrator composes again each time. The explicit list of authorized actions in the prompt is for the agent's own permission check, which sees the conversation, not the files that it names.

**One git worktree per Task, at `<repo>/.openloops/worktrees/<slug>`, on a new branch `ol-<slug>`.**
*Why:* Workers on the same repo must not collide, and a Worker's commits must never touch the Owner's own working tree. A new branch also avoids git's rule that one branch cannot be checked out twice.

**Workspaces are durable: reused on each Respawn, never deleted or force-overwritten.**
*Why:* a Workspace is the evidence of the Worker's work, and it may hold the Owner's own changes. A Respawn means "continue", never "start again". A clean start is the Owner's explicit act.

**Worker state goes in `<repo>/.openloops/<slug>/`, outside the worktree, and gitignored.**
*Why:* the notes must survive a git reset, a revert or a removed worktree, and must never be committed by mistake.

**Worker names are `ol-<slug>`, from the Spec file name.**
*Why:* a person can read `tmux ls` or `herdr agent list` and know which Task each Worker has. The prefix also lets the Orchestrator find its own Workers among the Owner's other sessions.

**The Worker writes the Tracker itself; the Orchestrator verifies and corrects.**
*Why:* the Worker knows best what it did, so it writes the comment (PR reference, results, blocker). A design where only the Orchestrator wrote the Tracker, from a result file, was tried on paper and dropped: it added a file format and lost the Worker's own words. The Orchestrator still checks the final state, because a Worker can forget a step.

**Completion is the Orchestrator's judgment,** from the Worker's screen, its Tracker comment and its implementation notes.
*Why:* no single signal is reliable. A Worker can be idle and not done, or done and still on screen. Several signals together, read by an agent, give the right answer.

**The Worker never exits by itself. The Orchestrator stops it.**
*Why:* a Worker that stays up can take the gap-fill prompt, and the Owner can read its screen. An exit with no comment would look like a crash.

**Workers write `implementation-notes.html`: a log of only what the Spec did not settle** (design decisions, deviations, tradeoffs, open questions, and a final summary).
*Why:* the Owner reads this before the diff. A play-by-play is too long to read; a log of the choices the Spec left open is exactly what a reviewer must check.

**Tracker comments read as if the Owner wrote them:** first person, short, no agent words.
*Why:* other people may see the Tracker. A work log in a normal engineer's voice is easy to read and does not leak how the work was done.

**A gap-fill prompt before completion, when the Spec has dependents.**
*Why:* a downstream Spec often has `{TBD: ...}` gaps that only the upstream work can answer. The Worker that just did that work is the best agent to fill them, while its context is still live.

**The Exploration Worker agent ships with the core.**
*Why:* Exploration Specs are core. They need a different agent: one that runs experiments in a loop, keeps a results file, and treats a failed experiment as a result, not a blocker.

## Specs and dependencies

**Two kinds of Spec: Build (acceptance criteria) and Exploration (hypothesis, metric, time budget).**
*Why:* a known deliverable and an open question end differently. A Build Spec ends when its criteria pass. An Exploration Spec ends when its time budget is used or its objective is met, and it always goes to In Review: findings need a human.

**The destination after a Worker depends on whether there is something for a human to look at,** not on the Spec kind.
*Why:* a PR, a report or a design proposal all need the Owner. Done is only for work that leaves nothing to review.

**A dependency is resolved only when the upstream Task is Done.** In Review does not count.
*Why:* code in review can still change. Downstream work against it would aim at a moving target. The Owner can override by moving the upstream Task to Done.

**Only leaf Tasks spawn.** A parent Task holds child Tasks, each with its own Spec.
*Why:* one Worker, one Spec, one Workspace. A parent that spawned would duplicate its children's work.

**Ready Tasks spawn in order of their number of dependents, most first.**
*Why:* an upstream Task that many others wait on frees the most work when it is Done.

**The Spec can be the Task body, a file in the project repo, or a wiki page.**
*Why:* a new Owner needs nothing but a Tracker to start. A central wiki helps an Owner with many related projects, so it is an optional module, not a requirement.

## Prompts and permissions

**Workers and the Orchestrator run in auto or bypass permission mode.**
*Why:* nobody is there to answer a prompt. Auto mode (an agent-side check of each action) is the recommended choice; bypass mode is only for a machine that is itself a sandbox. The docs put the warning next to the step that turns it on.

**Setup does not prescribe an allowlist.**
*Why:* the right allow rules depend on the Owner's agent, tools and risk. Setup settles them with the Owner instead.

**The Orchestrator answers an Input Request only when it is safe and the Spec makes the answer clear.** Otherwise it waits and notifies the Owner.
*Why:* a Worker that waits for hours on a simple prompt wastes the night. A Worker that gets a wrong "yes" can do harm. The rule takes the clear cases and leaves the rest to a human.

**After each answer, the Orchestrator drains the chain of prompts in the same Cycle,** up to about 10 times.
*Why:* a Worker often asks again one step later. If each answer waited for the next Cycle, one Task could stall for hours. The cap stops a runaway loop.

**Never send a key that stores a permanent permission rule or that destroys the prompt.**
*Why:* a permanent rule widens what every later Worker can do, with no review. A destroyed prompt takes away the Owner's chance to answer it.

**The Orchestrator runs only shell commands that never wait for input.**
*Why:* one command that waits (for example a `cp -i` alias) blocks the Cycle until `timeout` ends it, and the Cycle does no work.

## Review

**PRs open as drafts by default** (`review.md`: draft or ready).
*Why:* the Owner looks first. A GitHub draft is visible but does not ask reviewers. An Owner who trusts the pre-PR review can switch to ready.

**Review fixes are new commits on the same branch, with a reply to each Review comment.**
*Why:* a reviewer reads the incremental diff of each round. An amended or rebased commit hides what changed. A reply on each comment closes the conversation where the reviewer looks.

**Every Review comment is actionable, the Owner's own included.**
*Why:* the Worker opened the PR for the Owner, so the PR author's comments are Review comments too. Skipping them would leave the Owner with no way to comment on the PR.

**Comment-triggered Respawns are deduped by the last comment id; failed Checks are not.**
*Why:* with no dedup, every Cycle would trigger again on the same comment thread. A failed Check is different: the same commit can fail for a new reason (a flaky test, an upstream break), so the Worker gets a new try whenever no Worker is live, and it moves the Task to Blocked if it cannot fix it.

**No agent merges.** Approved, merged or closed means Done.
*Why:* the merge is the Owner's final control, and Owners merge in different ways (squash, keep commits, auto-merge). Approval means the reviewer is satisfied, so it is Done like a merge. A PR closed without merge is a decision too, so nothing is left.

**The Local branch Review System: the Task branch is the PR.** Review comments are Tracker comments with the Follow-up prefix; the Checks are the build and test command; Done is a merge into `main` or the Owner's move.
*Why:* the full Open Loop must work on one machine with no hosting service, for a first try and for the test fixture.

**Follow-ups are comments with an agreed prefix (default `ACTION:`), and their fulfilment is the Orchestrator's judgment.**
*Why:* the Owner can ask for more on a Task with results, without a new Task. A fixed rule (for example "any later comment fulfils it") would be brittle: a status comment is not a fulfilment. An agent can read the comments after the Follow-up and decide.

## Slots and Adapters

**Five Slots: Tracker, Host, Runtime, Notifier, Review System.**
*Why:* these are the places where one Owner's setup differs from another's. Everything else is the same for everyone and stays in the core.

**A Contract is a plain-language capability checklist, not an API.** The Owner's tools (a CLI, an MCP server) already exist; a notes file says how to use them.
*Why:* an API would need code for each tool and each agent. A checklist lets the setup agent check any tool, report the gaps, and write the notes file. The Orchestrator, as an agent, can follow a notes file directly.

**The core names no Slot product.**
*Why:* a product name in the core would make every other Owner edit the core. With the names only in notes files, the core is the same for everyone.

**Defaults are the most popular choice (for the Runtime, the recommended one: Herdr), and each Slot has a local fallback that needs no account.**
*Why:* most Owners already use the default (GitHub, cron, `claude`). The fallbacks let anyone try the full loop on one machine, and they are what the test fixture uses.

**The Markdown Tracker has no script.** The agents edit one file per Task directly.
*Why:* agents are good at editing Markdown. A script would be one more program to install and keep in step with the format.

**One Notifier, send only. The repo builds only the log file.**
*Why:* answers go through the Tracker (a Follow-up) or the Review System, which already keep a record. A Host with its own chat, or an MCP server for the Owner's chat tool, fills the Slot with no code in this repo.

**Silent mode: no message when nothing happened, never the same message twice.**
*Why:* a message on every Cycle trains the Owner to ignore all messages. Each message must mean something changed.

**A Slot tool failure sends one alert and stops the Cycle; recovery sends one message.**
*Why:* acting on half-read state can move Tasks wrongly. One alert for each outage (not one for each Cycle) keeps it from becoming noise. The pattern came from a login that expires; the generic form applies it to any Slot. A Notifier failure is only logged, because a Cycle can do its work without a message.

**Host, Runtime and Workspaces are on one machine.**
*Why:* the Orchestrator reads the Workers' screens and makes worktrees with local commands. A split across machines would need remote access in every Slot, for no gain in v0.1.

**A cap on live Workers (default 5).**
*Why:* each Worker costs tokens, memory and attention at review time. The cap keeps a full Ready column from overloading the machine or the budget.

## Setup and the repo

**Setup is a file of instructions for the Owner's own agent (`SETUP.md`), started with one prompt.**
*Why:* every Owner's machine is different, and an agent can explore it. It asks one question at a time with a recommended default, and never asks what a command can tell it.

**The repo holds placeholders only. Real values go to the home directory.**
*Why:* the repo is public and shared. A re-run of setup reads the notes files and changes only what the Owner asks, so a re-run never destroys a working setup.

**Third-party skills are installed from their source, never copied into the repo.** One data file lists them; the installer, the credits tables and `NOTICE` read it.
*Why:* the Owner gets the upstream version and its fixes, and the authors get credit. One list keeps the installer and the credits from drifting.

**`SPEC.md` is updated in the same change as a behavior change.**
*Why:* a spec that drifts from the prompts is worse than none: a reader trusts it and is wrong. The rule is in [`AGENTS.md`](../AGENTS.md), and a test checks that each Slot Contract checklist is the same in `SPEC.md` and in `adapters/`.

**Tests check only external results:** Task files, `state.json`, git branches, the Cycle log and the Notifier log.
*Why:* the Orchestrator is an LLM. Its words differ each run, but the files it leaves must not. A check on files stays true when a prompt is reworded.

**Keep today's behavior where it works.** The generic version was made by copying the daily prompts and removing the private parts, not by a rewrite.
*Why:* each rule came from a real failure. A rewrite would lose rules whose reason is no longer visible. Cleanup comes after v0.1, with the Cycle fixture to show what breaks.

**The words are fixed in `GLOSSARY.md`:** Task, not ticket; PR, not CR; In Review, not Awaiting Review.
*Why:* the prompts, the docs and the tests must use one word for one thing, or agents and readers guess. The name comes from the two loops: each Worker runs in its own Closed Loop until it is done, and the Orchestrator wraps it in the Open Loop of review and feedback, which stays open for new input until the Task is Done.
