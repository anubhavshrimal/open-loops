# Cycle fixture

Runs real Open Loops Cycles against sandboxes with the local fallbacks, then checks the results on disk.

Each scenario builds its own sandbox, a new temp directory with:

- a project repo and its local bare `origin` (made with `git clone --bare`, so the fixture runs no `git push`),
- a Markdown Tracker directory with the scenario's Tasks,
- a Spec directory with their Specs: small Build Specs made from `fixtures/build.spec.md`, or a Spec kept as its own file (`fixtures/shorten-fib.spec.md`),
- a home directory with the five example notes files from `adapters/`, filled in for the sandbox: Markdown Tracker, cron + `claude -p` Host, tmux Runtime (on the default tmux server), log-file Notifier, Local branch Review System. As setup does, the fixture also copies `core/agents/*.md` to `<home>/.claude/agents/`.

A scenario that starts in the middle of the Open Loop also makes what earlier Cycles would have left: the Task branch `ol-<slug>` in a worktree under `.openloops/worktrees/`, the Worker's PR comment on the Task (`Branch:`, `Commit:`, `Checks:`), and the `state.json` record. Between Cycles the fixture acts as the Owner where the scenario says so (it moves a Task to Done, merges a branch, adds a missing file).

Each Cycle runs the command in the "How a Cycle starts" block of the example `host.md`. Every Cycle must exit 0 and add a Cycle log entry. Every Worker name is unique across scenarios, because they all share the Runtime server.

## Scenarios

1. **`build`: a Ready Task reaches In Review.** After Cycle 1: the Worker `ol-hello-file` exists, `state.json` has its record and validates against `core/state.schema.json`, the Task is Working, and the Notifier log has a `spawned` line. At the end: the Task is In Review with a Tracker comment that names the branch, the branch has a commit with `hello.txt` (the Local branch Review System never pushes), and the Worker is closed.
2. **`exploration`: an Exploration Task reaches In Review.** The Spec is a tiny Exploration Spec with `agent: auto-researcher` and a 10-minute time budget: make `fib.py` shorter while `sh measure.sh` still passes (metric: its non-empty line count). After Cycle 1: the same checks as scenario 1 for `ol-shorten-fib`, plus the Worker was started with `--agent auto-researcher`. At the end: the Task is In Review with a Tracker comment that names the branch, the branch has a commit that is not in `main`, the state path `<project>/.openloops/shorten-fib/` has `results.tsv` (tab-separated header and at least one experiment row), `experiments-comparator.html` and the findings report `report.html` (the Spec's `report:` field is empty, so the default path), and the Worker is closed.
3. **`gated`: a Gated Task stays Ready.** `gate-down` depends on `gate-up`, which is In Review. Cycle 1 sends nothing, spawns no Worker and leaves `gate-down` in Ready. The Owner merges `gate-up` and moves it to Done; Cycle 2 spawns `gate-down` (a record in `state.json`, the Task Working or already In Review, a `spawned` line).
4. **`parent`: a parent Task with two child Tasks.** `family` has the children `fam-a` and `fam-b`; `fam-b` depends on `fam-a`, and its Spec has a `{TBD: ...}` gap that `fam-a`'s work fills. Only `fam-a` spawns. When the Orchestrator accepts its completion, `gap_fill_done` is `true`, the gap in `fam-b`'s Spec is filled, and the Spec was changed before the `in_review` line was sent. The Owner moves `fam-a` to Done; the next Cycle spawns `fam-b`. `family` never gets a Worker or a record and stays in Ready.
5. **`follow-up`: a Follow-up causes a Respawn.** `followup-file` is In Review with an Owner comment `ACTION: ...`. Cycle 1 starts `ol-followup-file` in the existing Workspace (no new worktree or branch), sends `respawned`, and leaves the Task Working with a `working` record (or both back at In Review).
6. **`merge`: a merge moves the Task to Done.** `merge-file` is In Review with an open branch. Cycle 1 has nothing to do and sends nothing. The Owner merges the branch into `main`; Cycle 2 moves the Task to Done, removes the record and sends `done`.
7. **`backlog`: Backlog is never touched.** A Backlog Task with a Spec and an `ACTION:` comment: after a Cycle the Task file is byte for byte the same, with no Worker, record, branch or message.
8. **`blocked`: a Blocked Task goes back to Ready.** `blocked-file` is Blocked on a missing file and the Owner was already told (`blocked_notified`). Cycle 1 sends nothing and the Task stays Blocked. The Owner adds the file to `main`; Cycle 2 moves the Task back to Ready, sends `unblocked`, and keeps the record with `blocked_notified` cleared.
9. **`tool-failure`: a Tracker tool failure.** The Tracker directory (with one Ready Task) is unreadable (`chmod 000`). Cycle 1 sends one `system_alert`, writes `alerts.tracker` and makes no other change. Cycle 2 sends nothing. The directory is made readable; Cycle 3 sends `system_recovered`, removes the alert and goes on with the Cycle (the Ready Task is spawned).

Scenarios 3, 6, 7, 8 and 9 each check at least one Cycle where nothing changed: the Notifier log must not grow.

## Run

Needs `git`, `tmux`, `timeout`, Python 3 (standard library only) and `claude` (logged in). The fixture uses a real agent and costs tokens, so run it on demand, not on each commit. The Workers run on your default tmux server (`tmux ls` shows them). If no server runs, the fixture starts one with a helper session `openloops-fixture-server` and stops that session at the end. Start the fixture from a normal shell: a tmux server that a sandboxed agent shell starts passes that sandbox to every Worker.

```sh
python3 tests/cycle_fixture/run_fixture.py                         # all 9 scenarios
python3 tests/cycle_fixture/run_fixture.py --scenario merge        # one scenario (repeat the option for more)
```

### Herdr instead of tmux

```sh
python3 tests/cycle_fixture/run_fixture.py --runtime herdr --scenario build
```

`--runtime herdr` puts the example `adapters/runtime/herdr.md` in the home directory instead of `tmux.md`. The scenarios and their checks stay the same; the Worker list is `herdr agent list`. Needs `herdr` in place of `tmux`. The fixture starts its own Herdr session `openloops-fixture` (a separate Herdr server, with a clean environment) and points every `herdr` command of the Cycles at it, so that the fixture never sees or touches your own Herdr agents. Watch the Workers with `herdr session attach openloops-fixture`. The fixture stops the session when all chosen scenarios pass, and keeps it for inspection when one fails (stop it with `herdr session stop openloops-fixture`).

Options: `--scenario` (default: all), `--runtime` (`tmux` or `herdr`, default `tmux`), `--orchestrator-model`, `--worker-model` (default `sonnet`), `--permission-mode` (default `auto`; the Orchestrator and the Workers run unattended, so they must never wait on a permission prompt), `--timeout-minutes` for the Worker phase of one scenario (default 45), `--interval-seconds`, the longest wait for a Worker between Cycles (default 120), `--cycle-timeout-minutes` (default 26). `--setup-only` builds one sandbox and prints its paths with no Cycle.

The fixture prints `SCENARIO <n> PASSED` or the failed checks for each scenario, then a summary that ends with `ALL <n> SCENARIOS PASSED` (exit 0) or `SOME SCENARIOS FAILED` (exit 1). It keeps every sandbox for inspection and prints its path.

## Offline checks

These need no agent:

```sh
python3 -m unittest discover -s tests/cycle_fixture
```

They check the state schema, the sandbox build and the scenario helpers, the Spec template fields, that `core/` names no Slot product, and that each Contract map row in `adapters/*/README.md` points at text in its example notes file.
