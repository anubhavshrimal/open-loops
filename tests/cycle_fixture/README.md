# Cycle fixture

Runs real Open Loops Cycles against a sandbox with the local fallbacks, then checks the results on disk.

The sandbox is a new temp directory with:

- a project repo and its local bare `origin` (made with `git clone --bare`, so the fixture runs no `git push`),
- a Markdown Tracker directory with one Ready Task (`hello-file` for scenario 1, `shorten-fib` for scenario 2),
- a Spec directory with that Task's Spec,
- a home directory with the five example notes files from `adapters/`, filled in for the sandbox: Markdown Tracker, cron + `claude -p` Host, tmux Runtime (on the default tmux server), log-file Notifier, Local branch Review System. As setup does, the fixture also copies `core/agents/*.md` to `<home>/.claude/agents/`.

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

## Scenario 2: an Exploration Task reaches In Review

The Spec is a tiny Exploration Spec with `agent: auto-researcher` and a 10-minute time budget: make `fib.py` shorter while `sh measure.sh` still passes (metric: its non-empty line count).

After Cycle 1: the same checks as scenario 1 for the Worker `ol-shorten-fib`, plus the Worker's tmux pane was started with `--agent auto-researcher`.

At the end:

- the Task is In Review, with a Tracker comment that names the branch `ol-shorten-fib`,
- the branch has a commit that is not in `main`,
- the state path `<project>/.openloops/shorten-fib/` has `results.tsv` (tab-separated header and at least one experiment row), `experiments-comparator.html` and the findings report `report.html` (the Spec's `report:` field is empty, so the default path),
- the Worker is closed.

## Run

Needs `git`, `tmux`, `timeout`, Python 3 (standard library only) and `claude` (logged in). The fixture uses a real agent and costs tokens, so run it on demand, not on each commit. The Worker `ol-<slug>` runs on your default tmux server (`tmux ls` shows it). If no server runs, the fixture starts one with a helper session `openloops-fixture-server` and stops that session at the end.

```sh
python3 tests/cycle_fixture/run_fixture.py                          # scenario 1
python3 tests/cycle_fixture/run_fixture.py --scenario exploration   # scenario 2
```

### Herdr instead of tmux

```sh
python3 tests/cycle_fixture/run_fixture.py --runtime herdr --permission-mode auto
```

`--runtime herdr` puts the example `adapters/runtime/herdr.md` in the home directory instead of `tmux.md`. Scenario 1 and its checks stay the same; the Worker list is `herdr agent list`. Needs `herdr` in place of `tmux`. The fixture starts its own Herdr session `openloops-fixture` (a separate Herdr server, with a clean environment) and points every `herdr` command of the Cycles at it, so that the fixture never sees or touches your own Herdr agents. Watch the Worker with `herdr session attach openloops-fixture`. The fixture stops the session when the scenario passes, and keeps it for inspection when it fails (stop it with `herdr session stop openloops-fixture`).

Options: `--runtime` (`tmux` or `herdr`, default `tmux`), `--orchestrator-model`, `--worker-model` (default `sonnet`), `--permission-mode` (default `bypassPermissions`: in `auto` mode the Orchestrator's classifier can deny the keys it sends to answer a Worker's prompts, and the Worker then never starts), `--timeout-minutes` (default 45), `--interval-seconds` between Cycles (default 120). `--setup-only` builds the sandbox and prints its paths with no Cycle.

The fixture prints `SCENARIO <n> (<name>) PASSED` and exits 0, or prints each failed check and exits 1. It keeps the sandbox for inspection and prints its path.

## Offline checks

These need no agent:

```sh
python3 -m unittest discover -s tests/cycle_fixture
```

They check the state schema, the sandbox build of both scenarios, the Spec template fields, that `core/` names no Slot product, and that each Contract map row in `adapters/*/README.md` points at text in its example notes file.
