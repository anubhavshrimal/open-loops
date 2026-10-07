---
title: "Add hello.txt"
type: source-summary
section: projects
tags: [task, example]
sources: []
created: 2026-10-07
updated: 2026-10-07
related: []
tracker_id: "hello-file"
report: ""
workspace: "{{PROJECT_REPO}}"
branch: "main"
depends_on: []
spec_status: "ready"
---

# Add hello.txt

## What

Add a file `hello.txt` at the root of the repo with one line: `Hello from Open Loops.`

## Why

This is the sample Build Spec. Setup uses it to verify a new install: one trivial Task goes through the Open Loop to In Review. The Cycle fixture uses it in its `build` scenario.

## Scope

- **Free to explore:** nothing else.
- **Out of scope:** any other file.

## Approach

Create the file, commit it on your branch, and follow the On Completion steps of the Worker rules.

## Task Breakdown

1. Add `hello.txt` with the one line `Hello from Open Loops.` Done when: the file has exactly that content.

## Boundaries

- ✅ Always: follow the Worker rules.
- ⚠️ Ask first: nothing.
- 🚫 Never: change other files in the repo.

## Constraints

None.

## Acceptance Criteria

- [ ] `hello.txt` exists on the Task branch with exactly one line, `Hello from Open Loops.`
- [ ] The build and test command passes.

## Context Links

None.

## Status

- [ ] Spec complete
- [ ] Implementation started
- [ ] Tests passing
- [ ] Context pages updated with results
- [ ] Tracker updated
