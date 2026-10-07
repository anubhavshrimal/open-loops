---
title: "Shorten fib.py"
type: source-summary
section: projects
tags: [exploration, fixture]
sources: []
created: 2026-10-07
updated: 2026-10-07
related: []
tracker_id: "shorten-fib"
report: ""
workspace: "{{PROJECT_REPO}}"
branch: "main"
agent: "auto-researcher"
depends_on: []
spec_status: "ready"
---

# Shorten fib.py

## Hypothesis

**Objective:** `fib.py` can be written in fewer non-empty lines and still print the same result. Any drop below the baseline is a meaningful improvement.

**Seed ideas** — starting points, not a plan. The agent is expected to go beyond these: form its own hypotheses, combine ideas, and change anything allowed below.

- Replace the index counter with a `for` loop — source: Owner
- Use tuple assignment for the two running values — source: Owner

## Search Space

Only the code of `fib.py`. Its command line (`python3 fib.py <n>` prints the n-th Fibonacci number) stays the same.

## Success Metric

- **eval_mode:** metric
- **Preference:** fewer lines, but still plain and readable Python.
- **Primary:** lines (count of non-empty lines in `fib.py`, lower is better)
- **Extraction:** `grep '^lines:' <log>`
- **Baseline:** run `sh measure.sh` on the unchanged code.

## Execution Environment

- **Run command:** `sh measure.sh`
- **Setup command:** none
- **Per-experiment time:** under 5 seconds

## Target Files

`fib.py`

## Read-Only Files

`measure.sh`, `check.sh`, `README.md`

## Time Budget

10 minutes in total, from the start of the session to In Review. Stop after at most 3 experiments after the baseline.

## Constraints

Python 3 standard library only. No new files except the results file.

## Prior Art

None.

## Reporting Format

`results.tsv` and `experiments-comparator.html` in the state path, and a short report at the default report path.

## Status

- [ ] Exploration started
- [ ] Initial results reported
- [ ] Promising direction identified
- [ ] Follow-up spec created
