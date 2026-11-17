# change-check.md part: Review System, GitHub PR

Only with the Change check (see [`docs/cost-saver.md`](../../docs/cost-saver.md)). This file goes with the example notes file [`github-pr.md`](github-pr.md). Setup copies the `## Review System` section below into `<home>/change-check.md`, and replaces each `{{...}}` placeholder with the value that it wrote into `<home>/review.md`. The Orchestrator never reads `change-check.md`.

## Review System

Each command only reads. Its output changes when a signal that the Orchestrator acts on changes, and only then. Tested live, read-only, with `gh` 2.96.0: stable over 3 runs. With more than one project in the Projects table of `review.md`, copy both reads for each GitHub repo, each with its own id (for example `prs-api`, `checks-api`).

### Auth probe

```sh
gh auth status --hostname github.com
```

### Read: prs

The open PRs from `ol-` branches: number, branch, head commit, draft, review decision, reviews (id and state), and the ids of the conversation comments and inline comments. A merged or closed PR leaves this list. Not read: times, comment text, Checks.

```sh
gh api graphql --paginate -F owner={{OWNER}} -F repo={{REPO}} -f query='query($owner: String!, $repo: String!, $endCursor: String) { repository(owner: $owner, name: $repo) { pullRequests(states: OPEN, first: 50, after: $endCursor, orderBy: {field: CREATED_AT, direction: ASC}) { pageInfo { hasNextPage endCursor } nodes { number headRefName headRefOid isDraft reviewDecision reviews(last: 100) { nodes { id state } } comments(last: 100) { nodes { id } } reviewThreads(last: 50) { nodes { comments(last: 20) { nodes { id } } } } } } } }' --jq '.data.repository.pullRequests.nodes[] | select(.headRefName | startswith("ol-")) | {number, branch: .headRefName, head: .headRefOid, isDraft, reviewDecision, reviews: [.reviews.nodes[] | [.id, .state]], comments: [.comments.nodes[].id], inline: [.reviewThreads.nodes[].comments.nodes[].id] | sort}'
```

### Read: checks

Failed Checks only: yes

For each open PR from an `ol-` branch with a failed Check on its latest commit: the PR number and the names of the failed Checks. A failed Check is one that "Read Checks" in `review.md` calls failed (`bucket` `fail` or `cancel`). A pending, running, passing or skipped Check prints nothing, so a Check that goes from pending to pass starts no Cycle.

```sh
gh api graphql --paginate -F owner={{OWNER}} -F repo={{REPO}} -f query='query($owner: String!, $repo: String!, $endCursor: String) { repository(owner: $owner, name: $repo) { pullRequests(states: OPEN, first: 50, after: $endCursor, orderBy: {field: CREATED_AT, direction: ASC}) { pageInfo { hasNextPage endCursor } nodes { number headRefName commits(last: 1) { nodes { commit { statusCheckRollup { contexts(first: 100) { nodes { __typename ... on CheckRun { name conclusion } ... on StatusContext { context state } } } } } } } } } } }' --jq '.data.repository.pullRequests.nodes[] | select(.headRefName | startswith("ol-")) | {number, failing: [.commits.nodes[].commit.statusCheckRollup.contexts.nodes[]? | select((.conclusion // .state) as $s | ["FAILURE", "ERROR", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE", "CANCELLED"] | index($s)) | (.name // .context)] | unique} | select(.failing != [])'
```
