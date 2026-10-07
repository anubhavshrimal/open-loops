---
title: "{Title}"
type: source-summary
section: projects
tags: [exploration, {domain-tags}]
sources: []
created: {date}
updated: {date}
related: []
tracker_id: ""   # the Tracker's id for the Task that points to this Spec
report: ""       # local Markdown or HTML path for the findings report (empty: <state-path>/report.html)
workspace: ""    # absolute path of the project repo (or directory) the Worker works in
branch: "main"   # branch to fork the Workspace from; leave empty for directory mode
agent: "auto-researcher"   # the Exploration Worker agent; runtime.md says how to start it
depends_on: []   # optional: Specs that must be Done first, e.g. ["setup-eval-harness"]
spec_status: "ready"   # "ready" | "deferred": deferred Specs have unresolved sections marked {TBD: reason}
---

# {Title}

## Hypothesis

**Objective:** {What are we trying to achieve? What does a meaningful improvement look like?}

**Seed ideas** — starting points, not a plan. The agent is expected to go beyond these: form its own hypotheses, combine ideas, and change anything allowed below.

- {idea} — {source: Owner / literature <link> / brainstorm}

## Search Space

{What the agent is free to change to reach the objective (everything not listed in Read-Only Files unless restricted here). What's explicitly out of scope.}

## Success Metric

- **eval_mode:** {metric | judgment}
- **Preference:** {in words — how you judge "better", what matters most, what would worry you}

If `metric`:
- **Primary:** {metric name} ({unit}, {lower/higher} is better)
- **Extraction:** `{grep pattern or parse command to extract from output}`
- **Baseline:** {current value to beat}
- **Secondary:** {optional metrics to track but not optimize for}

If `judgment`:
- **Raw outputs:** {where each run's outputs land, and how to read them}
- **Baseline outputs:** {path to baseline outputs to compare against}
- **Proxy metrics:** {optional numbers to record as supporting evidence — not the decision}

## Execution Environment

- **Run command:** `{exact command for one experiment}`
- **Setup command:** `{one-time setup, if any}`
- **Per-experiment time:** {wall clock estimate for one run}

## Target Files

{Files the agent CAN modify — be specific}

## Read-Only Files

{Eval harness, data, configs that must NOT change}

## Time Budget

{Total exploration budget: e.g., "4 hours", "overnight", "50 experiments max"}

## Constraints

{Fixed parameters: hardware, data, dependencies, things NOT to change, known dead ends to avoid}

## Prior Art

{Links to related context pages, papers, existing code, reports}

## Reporting Format

{What artifact to produce: "results.tsv with columns X,Y,Z", "HTML report with plots at the `report:` path", "context page update". Where does it go?}

## Status

- [ ] Exploration started
- [ ] Initial results reported
- [ ] Promising direction identified
- [ ] Follow-up spec created
