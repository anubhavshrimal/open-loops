# Cycle fixture

Runs real Open Loops Cycles against a sandbox with the local fallbacks, then checks the results on disk.

The sandbox is a new temp directory with:

- a project repo and its local bare `origin` (made with `git clone --bare`, so the fixture runs no `git push`),
- a Markdown Tracker directory with one Ready Task (`hello-file`),
- a Spec directory with a trivial Build Spec ("add a file hello.txt with one line"),
- a home directory with the five example notes files from `adapters/`, filled in for the sandbox: Markdown Tracker, cron + `claude -p` Host, tmux Runtime (on the default tmux server), log-file Notifier, Local branch Review System.

Each Cycle runs the command in the "How a Cycle starts" block of the example `host.md`.

## Scenario 1: a Ready Task reaches In Review

After Cycle 1:

- the tmux Worker `ol-hello-file` exists,
- `state.json` has its record and validates against `core/state.schema.json`,
- the Task is Working,
- the Notifier log has a `spawned` line.

The fixture then waits for the Worker and runs more Cycles until the scenario ends or the timeout. At the end:

- the Task is In Review, with a Tracker comment that names the branch `ol-hello-file`,
- the branch has a commit with `hello.txt` (the Local branch Review System never pushes),
- the Worker is closed.

## Run

Needs `git`, `tmux`, `timeout`, Python 3 (standard library only) and `claude` (logged in). The fixture uses a real agent and costs tokens, so run it on demand, not on each commit. The Worker `ol-hello-file` runs on your default tmux server (`tmux ls` shows it). If no server runs, the fixture starts one with a helper session `openloops-fixture-server` and stops that session at the end.

```sh
python3 tests/cycle_fixture/run_fixture.py
```

Options: `--orchestrator-model`, `--worker-model` (default `sonnet`), `--permission-mode` (default `bypassPermissions`: in `auto` mode the Orchestrator's classifier can deny the keys it sends to answer a Worker's prompts, and the Worker then never starts), `--timeout-minutes` (default 45), `--interval-seconds` between Cycles (default 120). `--setup-only` builds the sandbox and prints its paths with no Cycle.

The fixture prints `SCENARIO 1 PASSED` and exits 0, or prints each failed check and exits 1. It keeps the sandbox for inspection and prints its path.

## Offline checks

These need no agent:

```sh
python3 -m unittest discover -s tests/cycle_fixture
```

They check the state schema, the sandbox build, that `core/` names no Slot product, and that each Contract map row in `adapters/*/README.md` points at text in its example notes file.
