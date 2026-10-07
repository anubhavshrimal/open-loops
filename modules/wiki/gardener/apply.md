# Wiki gardener: apply approved items

Use this prompt when the Owner gives you a message that starts with `gardener YYYY-MM-DD:`. That message is the output of "Copy decisions" on a wiki gardener proposal page. It lists the approved, rejected and edited items, and the Owner's comments.

Do all work sequentially in this one context. Do NOT use subagents.

## Inputs

- `<wiki>`: the wiki directory, and `<home>`: the Open Loops home directory. The Owner's message or the handoff file names both.
- The handoff file `<home>/wiki-gardener/proposals/YYYY-MM-DD.md`. It holds each item with its exact change, evidence and verify step. Read its header first: it explains what the wiki is for.
- The Owner's decisions and comments from the message. A comment on an item is part of the instruction for that item.
- The ledger `<home>/wiki-gardener/ledger.jsonl`.
- `<home>/tracker.md`, for an item that changes the Tracker.

## Rules

- Apply only the items that the Owner approved or edited. For an edited item, the Owner's text replaces the `change` field where they differ.
- The Owner's approval of an item is the approval for the Tracker or doc write in that item. Make Tracker changes only with the tools in `tracker.md`. Do no other write outside the wiki.
- Do not force-push. Do not push. Commit in the wiki repo only.
- If an item is not clear, or its evidence is no longer true, skip it and write why. Do not guess.
- Write all text in short, plain sentences. Show all times in the Owner's local time with the UTC offset.

## Steps

1. Run `git -C <wiki> status --short`. If there are uncommitted changes that no item names, do not touch them. Stage only the files of each item.
2. For each approved or edited item, in `depends_on` order:
   1. Check the evidence again. If the state changed so that the change is wrong or not needed, mark the item `skipped` with the reason, and continue with the next item.
   2. Make the change.
      - Wiki: use `git mv` for moves. Then commit only the files of this item with the message `gardener(G-MMDD-n): <summary>`.
      - Tracker or a doc: make the exact change that the item gives.
   3. Do the `verify` step of the item. If the check fails, fix it once. If it still fails, revert the item's commit with `git revert --no-edit <sha>`, and mark the item `skipped` with the reason.
   4. Add a ledger line: `applied` with the commit sha (or the Task id or path for a change outside the wiki), or `skipped` with the reason. Write the same result under the item in the handoff file.
3. For each rejected item, add a `rejected` ledger line with the Owner's reason. The lint run does not propose the same fingerprint again.
4. If any wiki file changed: run `qmd update` if qmd indexes this wiki (`qmd status` lists a collection under `<wiki>`); do not touch another wiki's index. Add one entry to `wiki/log.md`: `## [YYYY-MM-DD] lint | Applied wiki gardener proposal YYYY-MM-DD`, with one line for each applied item. Commit it with the message `gardener(log): proposal YYYY-MM-DD`.
5. Clean up. If every item in the proposal now has a final status (applied, skipped, rejected or superseded), delete `proposals/YYYY-MM-DD.md` and `proposals/YYYY-MM-DD.html`. The ledger and the git history keep the record. If some items are still open, keep both files. The next lint run carries the open items over.
6. Reply to the Owner: the applied, skipped and rejected counts, one line for each skipped item with its reason, and the commit range.
