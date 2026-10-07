---
name: spec-exploration
description: Probe a research or exploration idea until it contains everything an autonomous agent needs to execute without human interaction. Use when the Owner wants to refine an exploration idea, says "grill for exploration", "probe this research", or is preparing an Exploration Spec for the auto-researcher agent (the Exploration Worker).
---

<!--
Attribution: parts of this skill are derived from mattpocock/skills
(https://github.com/mattpocock/skills), Copyright (c) 2026 Matt Pocock, MIT License.
Derived part: the "one question at a time, with your recommended answer" rule in
<what-to-do> follows the grilling skills. The probing phases, the saturation rule, the
completion criteria, the anti-patterns and the session flow are Open Loops' own (MIT, see
the Open Loops LICENSE).

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

Probe me relentlessly about this exploration/research idea until an autonomous agent could execute it overnight without asking a single question. Your goal is to extract everything the agent needs — objective, seed ideas, environment, evaluation, freedom and constraints — while leaving it free to explore beyond the seeds.

Ask questions one at a time, waiting for my answer before continuing. For each question, provide your recommended answer based on what you've learned so far.

If a question can be answered by exploring the codebase or reading existing files, do that instead of asking.

**Saturation rule:** Stop probing when 2 consecutive rounds yield no new information or constraints. At that point, declare the Spec ready and summarize what was captured.

**Output:** Append each Q&A to the raw idea file as the conversation progresses. The raw idea file becomes the full transcript.

</what-to-do>

<probing-protocol>

## Phase 1: Context & Background

Establish the landscape before diving into specifics.

- What problem are you trying to solve? What's the current state of things?
- What triggered this exploration now? Why is this the right time?
- What prior work exists? What's been tried before (by you or others)?
- What's the broader system this fits into? What upstream/downstream dependencies exist?
- Are there papers, blog posts, or existing implementations to reference?
- What's the team/project context? Who else cares about the outcome?

**Goal:** Understand the "why" deeply enough that the agent can make judgment calls during execution without asking.

## Phase 2: Objective & Seed Ideas

Clarify what the Owner wants to achieve and what they already have in mind. The seeds are starting points — the executing agent will go beyond them, so do not force them into a plan.

- What's the objective? What would a meaningful improvement look like?
- What ideas or hypotheses do you already have? Why do you think they might work?
- What would be a breakthrough vs an incremental improvement?
- What would make you say "stop, this direction is wrong"?

**Goal:** The agent knows what to aim for and has somewhere to start, without being told what to try.

### Literature & Brainstorm

Before moving on, broaden the seed list yourself. Dispatch a sub-agent to survey relevant literature, prior art and existing implementations, then brainstorm with the Owner on top of it. Add the resulting ideas to the Spec's seed list with their source (Owner / literature link / brainstorm). The executing agent starts from this list and does not repeat the survey.

## Phase 3: Execution Environment

Pin down exactly where and how experiments run.

- What workspace/repo will the agent work in? (exact path)
- What branch should it start from?
- What files can the agent modify? (target files — be specific)
- What files are read-only? (eval harness, data, configs that must not change)
- What's the one-time setup command? (install deps, prepare data, etc.)
- What's the run command for ONE experiment? (exact command)
- How long does one experiment take? (wall clock estimate)
- What hardware is available? (GPU type, memory, CPU cores)
- Are there resource constraints? (max GPU memory, max disk, max cost)
- What dependencies are needed? (packages, services, data files)
- Is there existing infrastructure the agent should use? (experiment tracking, logging)

**Goal:** A fresh agent should be able to `cd <workspace>`, run setup, and start experimenting immediately.

### Initial Setup Tasks

Before open-ended exploration begins, there may be deterministic boilerplate the agent must complete first. Probe for these:

- Are there any prerequisite tasks the agent must complete before exploration starts? (e.g., data preprocessing, model download, environment setup, creating evaluation harness)
- Are these tasks well-defined enough to be a checklist? (ordered steps with clear "done" conditions)
- Do any of these setup tasks require human review before proceeding to exploration?
- Is there existing code/infrastructure the agent should reuse, or must it build from scratch?

**Goal:** Separate the deterministic setup (do exactly this) from the open-ended exploration (try things). The agent executes setup tasks as a checklist before entering the experiment loop.

## Phase 4: Evaluation

Decide how the agent tells whether an experiment helped. Ask the Owner which mode fits:

- **`eval_mode: metric`** — a clean metric that can be trusted directly as a strict measure of improvement.
  - What's the PRIMARY metric? Direction?
  - How to extract it from output? (exact grep pattern, log line format, file to parse)
  - What's the current baseline value?
  - Are there SECONDARY metrics to track but not optimize for?
  - How noisy is it? How big a change counts as real (eval sample size, repeated runs)?
- **`eval_mode: judgment`** — improvement is judged by looking at raw outputs.
  - Where do each run's raw outputs land? How are they read?
  - Where are the baseline outputs to compare against?
  - In your own words: what makes an output better or worse? What matters most? What would worry you?
  - Are there proxy numbers worth recording as supporting evidence (not the decision)?

In both modes, capture the Owner's **preference** in words — how they would judge the result themselves. Do not ask for a fixed comparison sample or labelled examples; the agent analyzes results openly.

**Goal:** The agent knows how to judge an experiment without asking.

## Phase 5: Constraints & Boundaries

Define the guardrails — what the agent must NOT do.

- What's explicitly off-limits? (files, approaches, architectural changes)
- Known dead ends to avoid? (things that have been tried and failed)
- Budget: how many experiments total? (hard cap)
- Budget: total wall clock time? (e.g., "overnight = 8 hours max")
- Budget: cost constraints? (API calls, compute hours, tokens)
- Safety constraints? (don't touch prod data, don't modify shared resources)
- Must existing tests still pass? (guard command)
- Are there style/quality constraints? (code must pass linting, must be readable)
- What external systems must NOT be called? (prod APIs, databases)
- What's the rollback strategy if something goes badly wrong?

**Goal:** The agent knows its boundaries and won't accidentally break things or waste resources.

## Phase 6: Freedom & Domain Hints

Define what the agent is free to change, and give it knowledge — not a plan. The agent decides its own strategy: which ideas to pursue, whether to combine them, whether to run in parallel or serially.

- Beyond the read-only files, is anything else off-limits? (everything else is fair game)
- Are there domain heuristics, known tricks, or intuitions worth passing on?
- Is there anything you suspect but haven't tested?

**Goal:** The agent knows the boundaries of its freedom and the domain knowledge you have, then explores on its own.

## Phase 7: Edge Cases & Risks

Anticipate what could go wrong.

- What if the metric doesn't improve at all after many experiments?
- What if experiments crash repeatedly? (OOM, timeout, dependency failure)
- What if the baseline is already near-optimal?
- What external dependencies could block progress? (data availability, API limits)
- What assumptions might be wrong? (data distribution, hardware behavior)
- What if the search space is too large? How should the agent prioritize?
- Are there known instabilities? (non-deterministic results, flaky tests)
- What if the agent discovers something unexpected — should it pivot or stay on track?

**Goal:** The agent has contingency plans and won't loop without end.

## Phase 8: Handoff

The agent's standard outputs are fixed (ideas.md, experiments comparator, summary). Only ask:

- Should the agent open a PR with the best result?
- Anything beyond the standard outputs you want produced?
- What's the next step after this exploration? (full implementation? paper? another exploration?)

**Goal:** The agent knows whether anything beyond its standard outputs is expected.

</probing-protocol>

<completion-criteria>

The Exploration Spec is READY when ALL of the following are true:

1. **Run command is concrete** — not "run the training script" but `uv run train.py --config experiments/config.yaml`
2. **Evaluation is defined** — `eval_mode` declared with the Owner's preference. For `metric`: an extraction pattern that produces a number. For `judgment`: where raw outputs land and how to read them
3. **Baseline exists** — a known number (metric) or baseline outputs (judgment) to compare against
4. **Scope is bounded** — off-limits files listed; everything else is free to change
5. **Budget is defined** — the agent knows when to stop
6. **Seed ideas captured** — the objective plus seed ideas from the Owner and the literature/brainstorm step
7. **Failure modes are covered** — the agent knows what to do when things go wrong

If any of these are missing or vague, keep probing until they're concrete.

**Exception — deferred pieces of a multi-spec effort:** if this exploration is one piece of a larger effort split via spec-task's Split Checkpoint, and this piece depends on an earlier piece that hasn't run yet, it is allowed to be written with `spec_status: deferred` and unresolved criteria explicitly marked `{TBD: waiting on <earlier piece>}` instead of forcing premature answers. Do not guess a run command, metric, or budget just to satisfy this checklist — mark it TBD and move on. The Spec graduates to `spec_status: ready` (and this checklist applies in full) once the upstream piece completes and either resolves the gaps itself or provides enough new information for a fresh probing session to resolve them.

</completion-criteria>

<anti-patterns>

Do NOT accept these as answers — push for specifics:

- "Make it better" → Better how? What's the objective? What's the baseline?
- "Run the usual command" → What exact command? What arguments? What environment variables?
- "You'll know it when you see it" → Pick an `eval_mode`. For judgment, get the preference in words: what makes an output better or worse?
- "Whatever works" → Define constraints. Budget. Scope. Guardrails.
- "The standard approach" → Which standard? Link to docs. Show the command.
- "It should be obvious from the code" → Read the code now and confirm. State what you found.

</anti-patterns>

<session-flow>

**Multi-spec efforts:** if this exploration idea might decompose into multiple interdependent pieces (some deterministic setup, some open-ended search, some reporting), the split decision itself is made by **spec-task's Split Checkpoint**, not here — run that first. This skill only handles probing a single piece (which may itself be typed as an Exploration Spec, a Build Spec, or a mix across pieces) once the split decision (if any) is settled.

1. The Owner presents an idea (may be vague or detailed)
2. Read any existing raw idea file or Spec if referenced
3. Read the shared vocabulary in `GLOSSARY.md` (the project's, or the wiki's if the wiki module is on) — challenge any term conflicts during the session
4. Start with Phase 1 — establish context
5. Progress through phases, skipping questions already answered
6. If the Owner provides a brain dump, extract answers from it and only ask what's missing
7. Append each Q&A exchange to the raw idea file
8. **Update that `GLOSSARY.md` inline** when new terms are resolved — don't batch these up. Use the glossary format of the `domain-modeling` skill from mattpocock/skills (if it is not installed, install it from upstream: `npx skills add mattpocock/skills --skill domain-modeling -g -y`, or the `mattpocock-skills` Claude Code plugin). If the Owner uses a term that conflicts with existing vocabulary, call it out immediately.
9. When saturation is reached, summarize the captured Spec
10. Offer to write the complete Spec using the Exploration Spec template at `{{CORE_DIR}}/templates/exploration-spec.md`, where the Owner keeps Specs: a file in the project repo, a page in the wiki (if the wiki module is on), or the Task body; a Spec file needs a `Spec:` line in its Task. The Spec must be **self-contained** — any agent or person reading it cold should have full context to execute without referring back to the raw idea file. The raw file is the transcript; the Spec is the authoritative reference.

</session-flow>
