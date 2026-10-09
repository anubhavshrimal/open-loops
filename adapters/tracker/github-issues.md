# tracker.md: GitHub Issues Tracker

Example notes file for the Tracker Slot. Copy it to `<home>/tracker.md` and replace each `{{...}}` placeholder.

Tracker: GitHub Issues, through the `gh` CLI. A Task is an open or closed issue in one repo. The Orchestrator and the Worker use the Owner's `gh` login (`gh auth status` must show it).

Tracker repo: `{{TRACKER_OWNER}}/{{TRACKER_REPO}}`. Every command below passes `-R {{TRACKER_OWNER}}/{{TRACKER_REPO}}`; the Tracker repo can differ from the project repo.

Follow-up prefix: `ACTION:`

AI disclosure: off

## States

The state is one label on an open issue. Done is a closed issue. Pull requests are never Tasks (`gh issue list` does not return them).

| Core state | Native form |
|---|---|
| Backlog | open, with no `ol:` state label |
| Ready | open, label `ol:ready` |
| Working | open, label `ol:working` |
| Blocked | open, label `ol:blocked` |
| In Review | open, label `ol:in-review` |
| Done | closed (any close reason) |

A closed issue counts as Done, so a closed upstream Task resolves a dependency.

An open issue has at most one `ol:` state label. If you find two, use the first one in this order: `ol:blocked`, `ol:in-review`, `ol:working`, `ol:ready`. Then fix the labels with "Change state".

The Owner creates the four labels once (setup can run this for the Owner):

```sh
for l in ready working blocked in-review; do gh label create "ol:$l" -R {{TRACKER_OWNER}}/{{TRACKER_REPO}}; done
```

## Task body and the `Spec:` line

- The Task body is the issue body.
- Spec location: the first line of the body that starts with `Spec:` gives the Spec. The rest of that line is a path to a Spec file: relative to the project repo root, absolute, or a raw file URL. Example: `Spec: specs/add-hello-file.md`.
- With no `Spec:` line, the issue body is the Spec.
- The fields that spawn needs (`workspace`, `branch`, `depends_on`, `agent`) are frontmatter in the Spec file. When the body is the Spec, they are a front block at the top of the body, between two `---` lines. In `depends_on`, name upstream Tasks by issue number, for example `depends_on: ["#12", "#15"]`.

## Capabilities

- **Find Tasks in a state:**
  `gh issue list -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --state open --label ol:ready --limit 200 --json number,title,labels,url`
  Use the label of the state you look for. For Done, use `--state closed` and no label.
- **Read a Task's body:**
  `gh issue view <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --json number,title,body,state,labels,url`
- **Read a Task's comments:**
  `gh issue view <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --json comments --jq '.comments[] | {id, author: .author.login, createdAt, body}'`
  Comments come oldest first. The comment id is the `id` field.
- **Read a Task's children:** the issue's sub-issues.
  `gh issue view <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --json subIssues --jq '.subIssues.nodes[] | {number, title, state}'`
  A Task with one or more sub-issues is a parent Task. The parent of a child is in `--json parent` (`null` for a top-level Task).
- **Read a Task's dependencies:** the issue's "blocked by" relations, plus the `depends_on` field of its Spec (both count).
  `gh issue view <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --json blockedBy,blocking --jq '{blockedBy: [.blockedBy.nodes[] | {number, state}], blocking: [.blocking.nodes[] | {number, state}]}'`
  `blockedBy` lists the upstream Tasks; `blocking` lists the dependents. A dependency is resolved when the upstream issue's `state` is `CLOSED`.
- **Post a comment:**
  `gh issue comment <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --body-file <file>`
  Write the text to a file first, so that the shell does not change quotes or backticks.
- **Change state:** remove the old state label and add the new one in one command.
  `gh issue edit <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --remove-label ol:ready --add-label ol:working`
  Use the labels that the issue has now: `--remove-label` takes its current state label, and `--add-label` the new one.
  To Done (from any state): `gh issue edit <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --remove-label <current state label>`, then `gh issue close <n> -R {{TRACKER_OWNER}}/{{TRACKER_REPO}}`.
  Change nothing else on the issue (title, body, assignees, other labels).
- **Create a child Task:** a new issue that is a sub-issue of the parent `<n>`, in the state that you choose (its label; no label for Backlog). Write the body to a file first.
  `gh issue create -R {{TRACKER_OWNER}}/{{TRACKER_REPO}} --parent <n> --title "<title>" --body-file <file> --label ol:ready`
  `gh issue create` prints the new issue's URL; its number is the last part.

## Quirks

- The Orchestrator and the Worker comment as the Owner's GitHub user. A Follow-up is found only by its prefix, never by its author. Agents never start a comment with the Follow-up prefix.
- `gh issue list` returns 30 issues unless you pass `--limit`.
- More than one `--label` means "has all of these labels". Run one query for each state.
- A non-zero exit from `gh` (no login, network error, rate limit, missing repo) is a Tracker tool failure (see the core rule on Slot tool failure). Read the labels first, and remove only a label that the issue has.
- The Tracker comment voice of the Worker rules applies: the issue may be public.
