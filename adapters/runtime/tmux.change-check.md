# change-check.md part: Runtime, tmux

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`tmux.md`](tmux.md). Setup copies the `## Runtime` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/runtime.md`. The Orchestrator never reads `change-check.md`.

## Runtime

The command only reads. Tested offline on a private tmux server with a pane that does not change (`tests/cycle_fixture/test_change_check.py`); untested with a live agent screen. tmux has no login, so it has no Auth probe.

### Read: workers

For each `ol-` session: `working` when the output shows `esc to interrupt` (the screen of a working agent changes all the time, so it is not read). Otherwise the last 40 lines with text, so an Input Request, a new menu or an idle Worker changes the output. Gap: an agent screen that changes while it is not working (a clock, a counter) changes the output at each check and starts a Cycle each time, so check its stability first (`test`). With no tmux server, the read fails: the runner treats it as an error (one alert, at most one Cycle each Error gap), as the Cycle treats it as a Runtime tool failure.

```sh
s=$(tmux list-sessions -F '#{session_name}') || exit 1
printf '%s\n' "$s" | grep '^ol-' | sort | while read -r name; do
  out=$(tmux capture-pane -p -t "$name" -S -40) || exit 1
  if printf '%s\n' "$out" | grep -q 'esc to interrupt'; then
    printf '== %s working\n' "$name"
  else
    printf '== %s settled\n' "$name"
    printf '%s\n' "$out" | grep -v '^[[:space:]]*$'
  fi
done
```
