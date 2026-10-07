# Examples

A sample Build Spec and a sample Exploration Spec, each with a sample Markdown Task. Setup uses the Build sample to verify a new install (step 9 of [`SETUP.md`](../SETUP.md)). The Cycle fixture uses both samples in its `build` and `exploration` scenarios.

| Kind | Spec | Markdown Task | Project files it needs |
|---|---|---|---|
| Build | [`specs/hello-file.md`](specs/hello-file.md): add `hello.txt` with one line | [`tasks/hello-file.md`](tasks/hello-file.md) | none |
| Exploration | [`specs/shorten-fib.md`](specs/shorten-fib.md): make `fib.py` shorter, with `agent: auto-researcher` and a 10-minute time budget | [`tasks/shorten-fib.md`](tasks/shorten-fib.md) | [`files/fib.py`](files/fib.py) and [`files/measure.sh`](files/measure.sh), at the root of the project repo |

## Use a sample

1. Copy the Spec to a directory that the Workers can read (one of the `--add-dir` paths in `runtime.md`), and replace `{{PROJECT_REPO}}` with the absolute path of the project repo. Set `branch:` to the project's default branch if it is not `main`.
2. For the Exploration sample, commit `fib.py` and `measure.sh` at the root of the project repo first.
3. Make the Task:
   - Markdown Tracker: copy the Task file into the Task directory under the same name, and replace `{{SPEC_DIR}}` with the directory of the Spec.
   - Another Tracker: make a Task with the same title and body, in the Ready state, and set `tracker_id:` in the Spec to its id.

The next Cycle spawns a Worker for it.
