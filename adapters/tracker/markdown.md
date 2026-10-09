# tracker.md: Markdown Tracker

Example notes file for the Tracker Slot. Copy it to `<home>/tracker.md` and replace each `{{...}}` placeholder.

Tracker: Markdown files. One file per Task. The Orchestrator and the Worker read and edit the files directly with their file tools. There is no script and no server.

Task directory: `{{TRACKER_DIR}}`

Follow-up prefix: `ACTION:`

AI disclosure: off

## Task file format

A Task is the file `{{TRACKER_DIR}}/<task-id>.md`. The task id is the file name without `.md` (lowercase, digits and hyphens). Example:

```markdown
---
id: hello-file
title: Add hello.txt
state: Ready
parent: ""
depends_on: []
---

Spec: /path/to/specs/hello-file.md

Optional free text. If there is no Spec: line, this body is the Spec.

## Comments

### c1 | 2026-10-06T22:15:00-07:00 | owner
ACTION: also add a second line.
```

- `id`: same as the file name.
- `title`: the Task name.
- `state`: one of the six state names below, written exactly.
- `parent`: the id of the parent Task, or `""`.
- `depends_on`: the ids of upstream Tasks.
- Body: an optional `Spec:` line, then free text.
- `## Comments`: always the last section. Each comment is a `### <comment-id> | <timestamp> | <author>` heading, then the text. Comment ids are `c1`, `c2`, ... in order; a new comment takes the next number. Timestamps are ISO 8601 with UTC offset. Author is `owner` for the Owner and `worker` or `orchestrator` for agents.

## States

| Core state | Native value of `state:` |
|---|---|
| Backlog | `Backlog` |
| Ready | `Ready` |
| Working | `Working` |
| Blocked | `Blocked` |
| In Review | `In Review` |
| Done | `Done` |

This Tracker has no native close: only the state `Done` resolves a dependency.

## Capabilities

- **Find Tasks in a state:** read the frontmatter of every `*.md` file in the Task directory and keep those whose `state:` matches. Example: `grep -l '^state: Ready$' {{TRACKER_DIR}}/*.md`.
- **Read a Task's body:** read the file; the body is the text between the frontmatter and `## Comments`.
- **Read a Task's comments:** the `###` entries under `## Comments`, oldest first. The comment id is the first field of the heading.
- **Read a Task's children:** the Tasks whose `parent:` is this Task's id. Example: `grep -l '^parent: "\?<task-id>"\?$' {{TRACKER_DIR}}/*.md`.
- **Read a Task's dependencies:** the ids in its `depends_on:`. Its dependents are the Tasks whose `depends_on:` contains its id.
- **Post a comment:** append a new `### <next-id> | <timestamp> | <author>` heading and the text at the end of the file.
- **Change state:** edit the `state:` line in the frontmatter. Change nothing else in the frontmatter.
- **Create a child Task:** write a new file `{{TRACKER_DIR}}/<task-id>.md` with a new, unused id, `parent: <parent id>`, the state that you choose, the body, and an empty `## Comments` section (the format above).

## Quirks

- Edit only the file of the Task you act on, or the new file of a child Task that you create. Never rename or delete a Task file.
- Keep the frontmatter valid YAML: one key per line, strings with spaces in plain form (no quotes needed).
- If the Task directory does not exist or cannot be read, that is a Tracker tool failure (see the core rule on Slot tool failure).
