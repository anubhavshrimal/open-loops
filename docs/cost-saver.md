# Cost saver: the Change check

Instructions for the Owner's coding agent. Follow them when the Owner says yes to "Do you want me to check if you can save cost?" in [`SETUP.md`](../SETUP.md), or later when the Owner asks for it. At the end, give the Owner ONE recommendation.

By default, the Host starts a Cycle at a fixed interval (default 30 minutes), also when nothing changed. Each of these Cycles costs one agent session. The Change check ([`core/change-check.py`](../core/change-check.py)) is a script with no LLM. The Host runs it every 5 minutes instead. It runs the Read commands of `<home>/change-check.md`, hashes their output into the Change marker, and starts a Cycle only when the marker changed, a read failed, or the Safety Cycle is due. A check with no change costs no agent tokens. `change-check.md` is one file in the home directory that you assemble in step 2 from the example parts next to the example notes files (`<clone>/adapters/<slot>/<example>.change-check.md`). The Orchestrator never reads it, so a Cycle costs the same with or without it. The rules are in [`SPEC.md`](../SPEC.md) section 4, "When a Cycle starts". The words are in [`GLOSSARY.md`](../GLOSSARY.md).

In `<placeholders>` below, `<clone>` is the Open Loops clone and `<home>` is the home directory.

## 1. What to hash, and what not to hash

The Change marker must change when, and only when, the Orchestrator has something to do. A read that misses a signal delays that work to the next Safety Cycle. A read that prints noise starts Cycles that do nothing, and each one costs a full session.

Hash these: the signals that the Orchestrator acts on.

| Slot | Signal | Why |
|---|---|---|
| Tracker | each Task that is not in Backlog: its state, body, labels, comment ids and texts, children and their states, upstream Tasks and their states | a new Task, a state change, a Follow-up, a cleared dependency |
| Review System | each open `ol-` PR: its head, draft state, review decision, review ids, comment ids | a new Review comment, an approval, a merge, a close |
| Review System | each failing Check, by name (`Failed Checks only: yes`) | a Respawn on a failed Check |
| Runtime | each `ol-` Worker: its name, its id, its status; for an Input Request, the text of the prompt | a completion, an exit, an Input Request |
| (the runner adds) | `core/orchestrator.md` and the five notes files | a new rule must be applied |

Do not hash these:

| Do not hash | Why |
|---|---|
| "last modified" or "updated at" times | they change on any edit, also on fields that no action reads. In one live deployment, a time change started a Cycle that had nothing to do. |
| files that the Orchestrator or a Worker writes for itself (flags, notes, `state.json`) | each Cycle writes them, so the next check starts an echo Cycle, then retries. A hand edit of `state.json` takes effect at the next Cycle anyway. |
| the screen of a working agent, a clock, a counter, a spinner | they change at each check and start a Cycle each time |
| Spec files | a Spec edit needs no Cycle until the Task moves or gets a comment |
| files that the Orchestrator only passes to a Worker (for example a file that a Task names) | the Orchestrator does not act on their content; the Worker reads them |
| downstream Tasks (the Tasks that a Task blocks) | no action uses them |
| Backlog Tasks | the Orchestrator never reads them |
| passing or pending Checks | only a failing Check needs action |

More rules for a Read command:

- It only reads. It never writes to a Slot, and it never waits for input.
- It exits with a code that is not 0 when it cannot read. Put the read in a variable first (`out=$(cmd) || exit 1`): a pipe hides the exit code of the read.
- Its output is the same each time when nothing changed: sort lists, and leave out times and counters.
- A login failure must show in the Auth probe of the same part. The runner runs every Auth probe before each Cycle. When one fails, no Cycle starts until it passes: a Cycle with a failed login would only stop at its first step.

## 2. Evaluate

Do the steps in order. Stop at the first step that says "not a fit", and go to step 7.

### Step 1. Can the Host run the Change check?

Read the Host part `<clone>/adapters/host/<example>.change-check.md` of the Host in `<home>/host.md`.

- It must give "Run one Cycle and return its result": one command that waits for the Cycle's agent session, ends a hung Cycle, and exits with the session's exit code.
- The Host must run a command with no agent on a schedule.
- If the part says "not available", the Change check is not a fit.

| Host example | Change check |
|---|---|
| `cron-claude.md`, `cron-codex.md` | available |
| `kirocrew.md` | not available: no command waits for a run and returns its result |
| `openclaw.md` | not available: untested |

### Step 2. Which Slots can be read with no LLM?

Assemble `<home>/change-check.md`. It changes nothing for the Orchestrator and the Host, so it needs no yes. Start it with the line `# change-check.md`, then copy these sections, each from the part of the example that the Owner's notes file uses:

1. `## Settings` from the Host part.
2. `## Tracker` from the Tracker part.
3. `## Review System` from the Review System part.
4. `## Runtime` from the Runtime part.
5. `## Notifier` from the Notifier part, if it has one.

Replace each `{{...}}` placeholder with the value that setup wrote into the notes file of the same Slot. Check that no placeholder is left: `grep -n '{{' <home>/change-check.md` prints nothing.

| Example | Read commands | Tested |
|---|---|---|
| Tracker `github-issues.md` | `tasks`, Auth probe | live, read-only |
| Tracker `markdown.md` | `tasks` | offline |
| Review System `github-pr.md` | `prs`, `checks` (one pair for each project repo), Auth probe | live, read-only |
| Review System `local-branch.md` | `branches` | offline |
| Runtime `herdr-core.md` | `workers` | live, read-only |
| Runtime `tmux.md` | `workers` | offline, not with a live agent screen |
| Runtime `herdr.md` | `workers` | untested |

For a tool with no example, write the Read commands with the rules of section 1. If a Slot has a signal that no command can read with no LLM, write it down for step 6: that signal waits for the Safety Cycle.

The Notifier: if `change-check.md` has a `### Send` command, the runner sends its alerts with it. If it has none, its alerts go only to `<home>/change-check.log`. Write that down for step 6.

### Step 3. Test that the reads are stable

```sh
python3 <clone>/core/change-check.py test --home <home>
```

It runs each Auth probe once and each Read command 3 times. It must end with `stable` for each read and exit 0. For each read that is `NOT STABLE`, find the part of the output that changes (run the read twice and compare) and remove it from the read. If a read cannot be made stable, the Change check is not a fit.

The output also gives the time of each read (`ms=`). The sum must be well below the Change check interval of the crontab line (5 minutes in the examples).

### Step 4. One detection test (only with the Owner's yes)

This step writes to the Tracker. Ask the Owner first: "May I post one test comment on Task `<task>` and then delete it, to check that the Change check sees it?" With no yes, skip this step and tell the Owner that detection is not tested.

1. Run the test command and note the `marker=`.
2. Post the comment.
3. Run the test command again. The `marker=` must be different, and the read that changed must be the Tracker's.
4. Delete the comment.

### Step 5. Measure the cost of one Cycle

1. Read the cost of the last scheduled Cycle from the agent's own usage report (credits, or tokens and their price). Call it `C` credits.
2. Only if no report has it: ask the Owner, then run the Host's "Run one Cycle and return its result" command once, by hand, from `<home>`, just after a scheduled Cycle ended. It is a real Cycle: it can spawn Workers and write to the Tracker, and the fixed interval has no lock against a second Cycle.
3. Count the Cycles today: `24 × 60 / <interval in minutes>` (48 for 30 minutes).
4. Count the changes for each day: the `orchestrator.log` entries of the last days that did something (a spawn, a state change, a Respawn, a notice). With no history, use 10.

### Step 6. Compute the cost of each option

| Option | Cycles each day | Credits each day |
|---|---|---|
| Fixed interval (today) | `24 × 60 / <interval>` | Cycles × `C` |
| Change check | `24 × 60 / <Safety Cycle in minutes>` Safety Cycles + changes each day | Cycles × `C` (a check costs 0) |

Measured in one live deployment over 45 hours: 198 credits each day with a Cycle each 30 minutes, 26 credits each day with the Change check (20 Cycles). 39 % of those 20 Cycles had nothing to do. Three rules of this runner remove them: no Cycle while an Auth probe fails, no hash of its own files or of times, and a Cycle that exits 0 is not run again.

What the Change check loses or delays, against a Cycle each interval:

- A free-text blocker that clears outside the Tracker: seen only at the Safety Cycle.
- A change of who is a trusted author: seen only at the Safety Cycle.
- A repeated Respawn for the same Check that still fails: only on a change or the Safety Cycle (today: each Cycle).
- A Spec file edit: seen only with the next comment, Task change or Safety Cycle.
- Each signal that step 2 found no Read command for: seen only at the Safety Cycle. For example, with the Herdr Runtime (its read is untested): a second prompt with the same Worker status, or a status that it cannot classify.
- With no Send command: the Change check alerts go only to `change-check.log`.
- `system_recovered` after a Slot outage that only the Orchestrator sees: sent at the next Cycle.
- An echo Cycle after a Cycle that wrote to a Slot (a comment, a state change): one more Cycle, which finds nothing to do.
- With a Repeat limit hold (3 failed Cycles in a row): no Cycle until a change or the Safety Cycle.
- Known limit: exit 0 means that the Cycle's agent session ended, not that the Cycle did all its work. A Slot tool that fails during a Cycle (for example a server error of the Tracker) makes the Cycle send an alert and skip that Slot's work, and the session still exits 0. Then the change that started that Cycle waits for the next change or the Safety Cycle. The Auth probes before each Cycle make a login failure unlikely, not impossible: a login can expire during a Cycle, and some Slots have no Auth probe.

### Step 7. Give ONE recommendation

Tell the Owner the numbers of step 6, the list of what they lose or delay, and one recommendation:

- If a step said "not a fit", or the Change check saves less than the cost of one Cycle each day, or a lost signal in the list is one that the Owner needs at once: say "Keep the scheduled Orchestrator", give the credits each day of the fixed interval, and name the reason and the exact signals that the Change check would lose or delay.
- Else: recommend the Change check, with the credits each day of each option.

Change nothing until the Owner says yes.

## 3. Switch on, switch off

With the Owner's yes:

1. Check that `<home>/change-check.md` exists and that the test command of step 3 exits 0.
2. Replace the crontab line (or the Host's job) of "How a Cycle starts" with the crontab line of the `## Host` section of the Host part. Keep the `PATH` line.
3. After 1 hour, read `<home>/change-check.log`. Each line is one Change check: `UNCHANGED`, `CYCLE reasons=...`, `SUCCESS`, `FAILED`, `HOLD`, `AUTH`, `TRANSIENT`, `ERROR`, `DEFER`, `BUSY`, `CONFIG` or `NOTIFY`.

To switch off: put back the crontab line of "How a Cycle starts". The runner files (`change-check.md`, `change-check.json`, `change-check.log`, `change-check.lock`) can stay or be deleted; the Orchestrator never reads them. `change-check.log` grows by one line for each Change check (about 288 lines each day at 5 minutes): the Owner can delete it at any time.

## 4. Later

An Owner who said no at setup, or whose Slots changed, can run this evaluation at any time: tell the agent "Follow `<clone>/docs/cost-saver.md`". Run step 3 again after each change to `change-check.md` or a notes file.
