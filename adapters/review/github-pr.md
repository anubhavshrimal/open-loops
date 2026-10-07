# review.md: GitHub PR Review System

Example notes file for the Review System Slot. Copy it to `<home>/review.md` and replace each `{{...}}` placeholder.

Review System: GitHub pull requests, through `git` and the `gh` CLI. The PR is a GitHub PR from the Task branch `ol-<slug>` to the Spec's `branch` (the base branch). The Worker and the Orchestrator use the Owner's `gh` login.

Remote to push to: `origin` (the GitHub repo of each project in the table below). Never push to any other remote.

Open PRs as: draft (or `ready`; with `draft`, the Owner looks first and runs `gh pr ready <n>`; a draft PR is still visible on a public repo)

Review skill: `code-review` (from mattpocock/skills)

## Projects

| Project repo | GitHub repo | Build and test command |
|---|---|---|
| `{{PROJECT_REPO}}` | `{{OWNER}}/{{REPO}}` | `{{BUILD_TEST_COMMAND}}` |

## Worker capabilities

Run each command in the Workspace. `<base>` is the Spec's `branch`. `<owner>/<repo>` is the GitHub repo of the project in the table above.

- **Push a branch:** `git push -u origin ol-<slug>`
- **Open a PR:**
  - Open PRs as `draft`: `gh pr create --draft --base <base> --head ol-<slug> --title "<title>" --body-file <file>`
  - Open PRs as `ready`: the same command without `--draft`.
  - `gh pr create` prints the PR URL. That URL is the PR reference.
- **PR reference** (the form to put in Tracker comments): `PR: https://github.com/<owner>/<repo>/pull/<n>`. Every `gh pr` command takes the URL in place of `<n>`.
- **Push commits:** commit on the same branch, then `git push`. Never force-push and never rewrite commits that are already pushed: the Owner reads the new commits as an incremental diff.
- **Reply to a Review comment:** start every reply with the marker line `<!-- open-loops:worker -->`, then say what you did (with the commit SHA) or why you push back.
  - Inline comment (on a line of the diff): `gh api repos/<owner>/<repo>/pulls/<n>/comments/<comment-id>/replies -F body=@<file>`. Use the numeric inline comment id. If the comment has an `in_reply_to_id`, reply to that id instead: GitHub takes replies only to the first comment of a thread.
  - Conversation comment or review summary: `gh pr comment <n> --body-file <file>`, and quote the comment you answer.
- **Checks:** run the project's build and test command from the table above before each push. The GitHub Checks run by themselves on each push.

## Orchestrator capabilities

`<owner>/<repo>` is the GitHub repo of the project in the table above. Pass `-R <owner>/<repo>` to every `gh pr` command, or use the PR URL in place of `<n>`.

- **Read PR state:**
  `gh pr view <n> --json state,isDraft,reviewDecision,latestReviews,mergedAt,closedAt,headRefName,headRefOid`
  - `approved`: `state` is `OPEN`, and `reviewDecision` is `APPROVED` or any entry of `latestReviews` has `state` `APPROVED`. (`reviewDecision` is set only when a ruleset or branch protection requires reviews.)
  - `open`: `state` is `OPEN` (draft or ready) and the PR is not approved.
  - `merged`: `state` is `MERGED`.
  - `closed`: `state` is `CLOSED` (closed without merge).
- **Read Review comments with ids:** a PR has three kinds of Review comment. Read all three:
  - Conversation comments: `gh pr view <n> --json comments --jq '.comments[] | {id, author: .author.login, createdAt, body}'`
  - Review summaries: `gh pr view <n> --json reviews --jq '.reviews[] | select(.body != "") | {id, author: .author.login, state, submittedAt, body}'`
  - Inline comments: `gh api repos/<owner>/<repo>/pulls/<n>/comments --paginate --jq '.[] | {id, user: .user.login, created_at, path, line, in_reply_to_id, body}'`

  Merge the three into one list, oldest first. The time is `createdAt`, `submittedAt` or `created_at`.

  The comment id in this Review System is `<time>/<id>`, for example `2026-10-06T22:15:00Z/1234567`: the time, then the `id` field. Store this form in `last_comment_id`. A comment is new when its time is later than the time in `last_comment_id`. This still works when that comment was deleted.

  Skip every comment whose body starts with `<!-- open-loops:worker -->`: those are the Worker's own replies.
- **Read Checks** (on the latest commit of the PR):
  `gh pr checks <n> --json name,state,bucket,link,workflow`
  - Failed: any Check with `bucket` `fail` or `cancel`.
  - Pending: any Check with `bucket` `pending`, and none failed.
  - Passing: every Check has `bucket` `pass` or `skipping`, or the PR has no Checks.
  - The Worker reads the log of a failed Check with `gh run view <run-id> -R <owner>/<repo> --log-failed`; the run id is the number after `/runs/` in the Check's `link`. A Check from an outside service has no `/runs/` in its link: open the link instead.

## Triggers

- New Review comment, or a failed Check → Respawn.
- `approved` or `merged` → Done.
- `closed` without merge → Done.

## Quirks

- The Worker never runs `gh pr merge`, `gh pr review --approve` or `gh pr ready`, and never changes repo settings, branch protection or rulesets. The Owner merges.
- The Worker opens the PR with the Owner's login, so the Owner is the PR author. GitHub does not let an author approve their own PR. For a solo Owner, Done comes from the merge or the close.
- `gh pr checks` exits non-zero when a Check failed (exit 1) or is pending (exit 8). Read the JSON, not the exit code. Its message "no checks reported" means no Checks.
- Any other non-zero exit from `gh` (no login, network error, rate limit, missing PR) is a Review System tool failure (see the core rule on Slot tool failure).
