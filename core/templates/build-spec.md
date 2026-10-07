---
title: "{Title}"
type: source-summary
section: projects
tags: [task, {domain-tags}]
sources: []
created: {date}
updated: {date}
related: []
tracker_id: ""   # the Tracker's id for the Task that points to this Spec
report: ""       # optional: local Markdown or HTML path for a written report
workspace: ""    # absolute path of the project repo (or directory) the Worker works in
branch: "main"   # branch to fork the Workspace from; leave empty for directory mode
depends_on: []   # optional: Specs that must be Done first, e.g. ["setup-data-pipeline"]
spec_status: "ready"   # "ready" | "deferred": deferred Specs have unresolved sections marked {TBD: reason}
---

# {Title}

## What

{Clear deliverable. What does "done" look like?}

## Why

{Context and motivation. Why now? What does this unblock?}

## Scope

- **Free to explore:** {things the Worker CAN do without asking: refactoring adjacent code, adding tests, improving error handling, etc.}
- **Out of scope:** {things this Task explicitly does NOT include}

## Approach

{Known approach or steps. If multiple options were considered, note the chosen one and why. Include decisions already made that the Worker must not re-decide.}

## Task Breakdown

{Ordered sub-tasks. Each should be independently verifiable.}

1. {Step 1}: done when: {testable condition}
2. {Step 2}: done when: {testable condition}
3. {Step 3}: done when: {testable condition}

## Boundaries

- ✅ Always: {actions the Worker should take without asking}
- ⚠️ Ask first: {actions requiring Owner approval}
- 🚫 Never: {hard stops for this specific Task}

## Constraints

{Non-negotiables: compatibility, performance, dependencies, things NOT to break}

## Acceptance Criteria

{Specific, testable conditions that must be true when complete. Include verification commands/checks.}

## Context Links

{Related pages, reports, Tasks, code locations}

## Status

- [ ] Spec complete
- [ ] Implementation started
- [ ] Tests passing
- [ ] Context pages updated with results
- [ ] Tracker updated
