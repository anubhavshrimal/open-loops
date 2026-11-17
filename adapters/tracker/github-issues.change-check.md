# change-check.md part: Tracker, GitHub Issues

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`github-issues.md`](github-issues.md). Setup copies the `## Tracker` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/tracker.md`. The Orchestrator never reads `change-check.md`.

## Tracker

Each command only reads. Its output changes when a signal that the Orchestrator acts on changes, and only then. Tested live, read-only, with `gh` 2.96.0: stable over 3 runs.

### Auth probe

```sh
gh auth status --hostname github.com
```

### Read: tasks

The open Tasks in Ready, Working, Blocked and In Review: number, name, body, state labels, comments (id and text), children and upstream Tasks (number and state). Not read: Backlog Tasks, times, downstream Tasks.

```sh
gh api graphql --paginate -F owner={{TRACKER_OWNER}} -F repo={{TRACKER_REPO}} -f query='query($owner: String!, $repo: String!, $endCursor: String) { repository(owner: $owner, name: $repo) { issues(states: OPEN, first: 50, after: $endCursor, labels: ["ol:ready", "ol:working", "ol:blocked", "ol:in-review"], orderBy: {field: CREATED_AT, direction: ASC}) { pageInfo { hasNextPage endCursor } nodes { number title body labels(first: 20) { nodes { name } } comments(last: 100) { nodes { id body } } subIssues(first: 50) { nodes { number state } } blockedBy(first: 50) { nodes { number state } } } } } }' --jq '.data.repository.issues.nodes[] | {number, title, body, labels: [.labels.nodes[].name] | sort, comments: [.comments.nodes[] | [.id, .body]], children: [.subIssues.nodes[] | [.number, .state]] | sort, upstream: [.blockedBy.nodes[] | [.number, .state]] | sort}'
```
