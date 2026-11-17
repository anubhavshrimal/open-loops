# change-check.md part: Review System, Local branch

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`local-branch.md`](local-branch.md). Setup copies the `## Review System` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/review.md`. The Orchestrator never reads `change-check.md`.

## Review System

The command only reads. Review comments and the `Checks:` line are Tracker comments, so the Tracker's read covers them. Tested offline (`tests/cycle_fixture/test_change_check.py`). The Local branch has no login, so it has no Auth probe.

### Read: branches

The head commit of `main` and of each `ol-` branch. A new commit, a merge into `main` or a deleted branch changes the output.

```sh
git -C {{PROJECT_REPO}} for-each-ref --format='%(refname:short) %(objectname)' refs/heads/main 'refs/heads/ol-*'
```
