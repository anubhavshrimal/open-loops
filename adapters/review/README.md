# Review System Slot

The Review System holds PRs, Review comments and Checks.

## Contract

The Worker must be able to:

- [ ] Publish a branch (push it, upload it with a review tool, or nothing).
- [ ] Open a PR (as a draft or as ready, per `review.md`).
- [ ] Publish more commits to the PR.
- [ ] Reply to a Review comment.

The Orchestrator must be able to:

- [ ] Read a PR's state: open, approved, merged, closed.
- [ ] Read a PR's Review comments, each with an id and its author.
- [ ] Tell whether an author is trusted (the Owner, or a user with write access).
- [ ] Read a PR's Checks.

`review.md` also says:

- [ ] `Open PRs as: draft | ready` (default: draft).
- [ ] The remote to push to, if the Review System pushes.
- [ ] `Review rounds: new commits | amend` (default: new commits).
- [ ] `AI disclosure: off | <text>` (default: off).
- [ ] The form of a PR reference in Tracker comments.
- [ ] The review skill the Worker runs before it opens the PR (default: `code-review` from mattpocock/skills).
- [ ] The build and test command of each project.

Triggers the core applies to every Review System: a new Review comment or a failed Check → Respawn; approved or merged → Done; closed without merge → Done. Setup makes no repo settings or rulesets. No agent ever merges.

## Example notes files

| Example | Review System |
|---|---|
| [`github-pr.md`](github-pr.md) | GitHub PR through `gh` (default) |
| [`local-branch.md`](local-branch.md) | Local branch: the Task branch is the PR (local fallback, no hosting service) |

## Contract map: `github-pr.md`

| Capability | Line in `github-pr.md` |
|---|---|
| Publish a branch | Worker capabilities: "Publish a branch" |
| Open a PR | Worker capabilities: "Open a PR" |
| Publish more commits | Worker capabilities: "Publish more commits" |
| Reply to a Review comment | Worker capabilities: "Reply to a Review comment" |
| Read PR state | Orchestrator capabilities: "Read PR state" |
| Read Review comments with ids | Orchestrator capabilities: "Read Review comments with ids" |
| Tell whether an author is trusted | Orchestrator capabilities: "Tell whether an author is trusted" |
| Read Checks | Orchestrator capabilities: "Read Checks" (Worker side: "Checks") |
| Open PRs as | "Open PRs as" line |
| Remote | "Remote to push to" line |
| Review rounds | "Review rounds" line |
| AI disclosure | "AI disclosure" line |
| PR reference | Worker capabilities: "PR reference" |
| Review skill | "Review skill" line |
| Build and test command | "Projects" table |
| Triggers (Respawn, Done) | "Triggers" section |

## Contract map: `local-branch.md`

| Capability | Line in `local-branch.md` |
|---|---|
| Publish a branch | Worker capabilities: "Publish a branch" |
| Open a PR | Worker capabilities: "Open a PR" |
| Publish more commits | Worker capabilities: "Publish more commits" |
| Reply to a Review comment | Worker capabilities: "Reply to a Review comment" |
| Read PR state | Orchestrator capabilities: "Read PR state" |
| Read Review comments with ids | Orchestrator capabilities: "Read Review comments with ids" |
| Tell whether an author is trusted | Orchestrator capabilities: "Tell whether an author is trusted" |
| Read Checks | Orchestrator capabilities: "Read Checks" (Worker side: "Checks") |
| Open PRs as | "Open PRs as" line |
| Remote | "Remote to push to" line |
| Review rounds | "Review rounds" line |
| AI disclosure | "AI disclosure" line |
| PR reference | Worker capabilities: "PR reference" |
| Review skill | "Review skill" line |
| Build and test command | "Projects" table |
