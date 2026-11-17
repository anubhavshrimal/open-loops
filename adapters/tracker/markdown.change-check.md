# change-check.md part: Tracker, Markdown files

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`markdown.md`](markdown.md). Setup copies the `## Tracker` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/tracker.md`. The Orchestrator never reads `change-check.md`.

## Tracker

The command only reads. Its output changes when a Task file that is not in Backlog changes, and only then. Tested offline (`tests/cycle_fixture/test_change_check.py`). This Tracker has no login, so it has no Auth probe.

### Read: tasks

```sh
[ -d {{TRACKER_DIR}} ] || exit 1
for f in {{TRACKER_DIR}}/*.md; do
  [ -e "$f" ] || continue
  grep -qx 'state: Backlog' "$f" && continue
  printf '== %s\n' "$f"
  cat "$f" || exit 1
done
```
