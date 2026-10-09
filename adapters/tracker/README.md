# Tracker Slot

The Tracker stores Tasks and their states. The core needs only the Tracker; a wiki is never required.

## Contract

A Tracker must let the Orchestrator and the Worker:

- [ ] Find the Tasks in a state.
- [ ] Read a Task's body.
- [ ] Read a Task's comments, each with an id and its author.
- [ ] Tell whether an author is trusted (the Owner, or a user with write access).
- [ ] Read a Task's children.
- [ ] Read a Task's dependencies (and its dependents).
- [ ] Post a comment on a Task.
- [ ] Change a Task's state.
- [ ] Create a child Task under a Task.

`tracker.md` holds the tools for each capability, the map from the six core states (Backlog, Ready, Working, Blocked, In Review, Done) to the native names, the IDs, the Follow-up prefix, the AI disclosure line (`AI disclosure: off | <text>`, default off), and the quirks of the tool.

Rules that the core applies to every Tracker:

- Spec location: a `Spec:` line in the Task points to a Spec file (in the project repo or in a wiki). Without it, the Task body is the Spec. The fields that spawn needs (`workspace`, `branch`, `depends_on`, `agent`) are frontmatter in a Spec file, or a front block at the top of the Task body.
- Only leaf Tasks spawn. A parent Task with children never spawns itself.
- A dependency counts as resolved only when the upstream Task is Done (a Tracker with a native close says in `tracker.md` whether a closed Task counts as Done).
- Whether a Follow-up is fulfilled is the Orchestrator's judgment, from the comments after it.

## Example notes files

| Example | Tracker |
|---|---|
| [`github-issues.md`](github-issues.md) | GitHub Issues through `gh` (default) |
| [`markdown.md`](markdown.md) | Markdown files: one file per Task (local fallback, no account) |

## Contract map: `github-issues.md`

| Capability | Line in `github-issues.md` |
|---|---|
| Find the Tasks in a state | Capabilities: "Find Tasks in a state" |
| Read a Task's body | Capabilities: "Read a Task's body" |
| Read a Task's comments, with ids | Capabilities: "Read a Task's comments" |
| Tell whether an author is trusted | Capabilities: "Tell whether an author is trusted" |
| Read a Task's children | Capabilities: "Read a Task's children" |
| Read a Task's dependencies and dependents | Capabilities: "Read a Task's dependencies" |
| Post a comment | Capabilities: "Post a comment" |
| Change a Task's state | Capabilities: "Change state" |
| Create a child Task | Capabilities: "Create a child Task" |
| Map of the six states | "States" table |
| Follow-up prefix | "Follow-up prefix" line |
| AI disclosure | "AI disclosure" line |
| `Spec:` line rule | "Task body and the `Spec:` line" |

## Contract map: `markdown.md`

| Capability | Line in `markdown.md` |
|---|---|
| Find the Tasks in a state | Capabilities: "Find Tasks in a state" |
| Read a Task's body | Capabilities: "Read a Task's body" |
| Read a Task's comments, with ids | Capabilities: "Read a Task's comments" |
| Tell whether an author is trusted | Capabilities: "Tell whether an author is trusted" |
| Read a Task's children | Capabilities: "Read a Task's children" |
| Read a Task's dependencies and dependents | Capabilities: "Read a Task's dependencies" |
| Post a comment | Capabilities: "Post a comment" |
| Change a Task's state | Capabilities: "Change state" |
| Create a child Task | Capabilities: "Create a child Task" |
| Map of the six states | "States" table |
| Follow-up prefix | "Follow-up prefix" line |
| AI disclosure | "AI disclosure" line |
