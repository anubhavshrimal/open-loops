---
name: spec-task
description: Spec-driven development grill for Open Loops Task creation. Combines domain model sharpening with spec-driven decomposition — scope definition, task breakdown, boundary identification, and verification criteria. Use when refining a raw idea into a Build Spec that a Worker can run without a human.
---

<!--
Attribution: parts of this skill are derived from mattpocock/skills
(https://github.com/mattpocock/skills), Copyright (c) 2026 Matt Pocock, MIT License.
Derived parts: the interview opening in <what-to-do> (from the grilling skills) and the
"Domain awareness" and "During the session" rules in <supporting-info> (from the
`domain-modeling` skill). The split checkpoint, deferred Specs and the spec-driven
decomposition phases are Open Loops' own (MIT, see the Open Loops LICENSE).

The MIT License of mattpocock/skills:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for an answer to each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

After the core plan is solid (What/Why/Approach/Constraints), proceed to the **split checkpoint** below before entering spec-driven decomposition.

</what-to-do>

<split-checkpoint>

## Split Checkpoint (run once, right after the core plan)

Before decomposing into task-breakdown steps for a single Spec, check whether this idea is actually **multiple interdependent efforts** rather than one Task. Signs it should split: the pieces would run in genuinely different sessions/contexts, a later piece's approach can't be decided until an earlier piece finishes, or the pieces are big enough that grilling them together would blur focus (the "one agent doing multiple things" problem).

Ask: *"This looks like it could be [N] pieces: {name each piece in one line}. Do you want these as separate Specs, or is this one coherent Task?"*

**If one Task:** proceed directly to the existing spec-driven decomposition phases below, unchanged.

**If split:** for each piece, classify it into exactly one state:

- **Now** — sharp enough to grill immediately. Run the full spec-driven decomposition phases below, scoped ONLY to this piece. Produces a complete Spec with `spec_status: ready`.
- **Later** — you know it exists and roughly what it's for, but real details depend on an earlier piece finishing first (a dependency). Do NOT grill this piece now. Write a minimal Spec immediately anyway — use the Build Spec or Exploration Spec template, fill in only `## What`/`## Why` with the one-line gist and mark every other section `{TBD: waiting on <earlier piece name>}`. Set `spec_status: deferred` and `depends_on: ["<earlier-piece-spec>"]` in frontmatter.

Every piece — Now or Later — gets its own Spec file and its own child Task under the parent Task in the Tracker, created immediately (the parent Task holds one child Task for each piece, and each child Task points to its own Spec). Deferred pieces are not skipped or held back from the Tracker; they exist as placeholder child Tasks so dependency chains are visible and trackable from the start.

**Piece typing:** each piece is independently typed as a Build Spec or an Exploration Spec based on its own nature — do not assume every piece inherits the parent idea's type. A piece that is deterministic setup/harness work is a Build Spec even if a sibling piece is an open-ended Exploration Spec.

**Graduating a deferred piece:** when the piece(s) it depends on complete, and the completing Worker's end-of-session gap-fill pass (the Orchestrator's gap-fill re-prompt) has resolved its TBD markers, the deferred Spec is re-run through the full decomposition phases (grilled properly, TBD markers replaced with real content) and flipped to `spec_status: ready`. This can happen inline in the same session as the upstream completion write-up, or as a fresh session later — either way, do not grill a deferred piece until its TBD markers are gone or you have enough new information to resolve them yourself.

</split-checkpoint>

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `GLOSSARY-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── GLOSSARY-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── GLOSSARY.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── GLOSSARY.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `GLOSSARY.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the Owner uses a term that conflicts with the existing language in `GLOSSARY.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the Owner uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the Owner to be precise about the boundaries between concepts.

### Cross-reference with code

When the Owner states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update GLOSSARY.md inline

When a term is resolved, update `GLOSSARY.md` right there. Don't batch these up — capture them as they happen. Use the glossary format of the `domain-modeling` skill from mattpocock/skills. This module does not copy that format: if the skill is not installed, install it from upstream (`npx skills add mattpocock/skills --skill domain-modeling -g -y`, or the `mattpocock-skills` Claude Code plugin).

Don't couple `GLOSSARY.md` to implementation details. Only include terms that are meaningful to domain experts.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the ADR format of the `domain-modeling` skill (install it from upstream, as above).

</supporting-info>

<spec-driven-decomposition>

## Spec-Driven Decomposition Phases

After the core plan (What/Why/Approach/Constraints) is established, probe these areas to produce a complete Spec that a Worker can run. Ask questions one at a time.

### Phase 1: Scope Definition

Probe for both what the Worker IS free to do and what it must NOT touch:

- "What adjacent code/systems is the Worker free to modify without asking? (e.g., refactoring nearby code, adding tests, improving error handling)"
- "What is explicitly out of scope for this Task?"
- "Are there any files, modules, or systems the Worker should treat as read-only?"

Goal: Produce a clear `## Scope` section with `Free to explore:` and `Out of scope:` subsections.

### Phase 2: Task Breakdown

Probe for decomposition into independently verifiable steps:

- "Can this be broken into steps that are each independently verifiable?"
- "What's the dependency order — which steps must complete before others can start?"
- "Could any of these steps run in parallel?"
- "For each step, what does 'done' look like? (specific, testable condition)"

Goal: Produce a numbered `## Task Breakdown` section where each item has a clear completion condition.

### Phase 3: Boundary Identification

Probe for the three-tier boundary system (Always / Ask First / Never):

- "What should the Worker always do without asking? (e.g., run tests after changes, follow existing patterns)"
- "What actions need your approval before the Worker proceeds? (e.g., adding dependencies, changing schemas, modifying shared interfaces)"
- "Are there any hard stops — things the Worker must never do regardless of context?"

Goal: Produce a `## Boundaries` section with ✅ Always / ⚠️ Ask first / 🚫 Never tiers.

### Phase 4: Verification Criteria

Probe for how completion will be verified (beyond just acceptance criteria):

- "How should the Worker prove the work is done? (specific tests, commands, output checks)"
- "Are there edge cases that must be explicitly tested?"
- "What would a reviewer check first when looking at this PR?"

Goal: Strengthen the `## Acceptance Criteria` section with concrete verification commands/checks.

### Phase 5: Prior Decisions

Probe for decisions already locked in that the Worker must not re-decide:

- "Are there any architectural or design decisions already made that the Worker must follow? (e.g., chosen library, data model, API shape)"
- "Any past approaches that were tried and rejected? (dead ends to avoid)"

Goal: Capture in `## Approach` or `## Constraints` — things the Worker must not second-guess.

## Output

After all phases, write the complete Spec using the Build Spec template at `{{CORE_DIR}}/templates/build-spec.md`. Write it where the Owner keeps Specs: a file in the project repo, a page in the wiki (if the wiki module is on), or the Task body; a Spec file needs a `Spec:` line in its Task. The Spec must be self-contained — any Worker reading it cold should have full context to execute without referring back to the raw idea file or this conversation.

</spec-driven-decomposition>
