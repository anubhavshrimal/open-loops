# LLM Wiki — Agent Schema

> This file is the operating manual for any LLM agent working on this wiki. Read it fully before doing anything.

## 1. Project Overview

This is a personal knowledge wiki — a **memory palace** — maintained by LLM agents on behalf of the Owner. Inspired by [Andrej Karpathy's "LLM Wiki" pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), it turns scattered sources into a structured, searchable, ever-growing knowledge base. It is also the central brain for the Owner's projects: Specs, decisions, glossary terms, hubs and results written back after Done live here, so the Owner does not give the same context again and again.

The system has three layers:

| Layer | Purpose | Mutability |
|-------|---------|------------|
| `raw/` | Original source material (PDFs, notes, transcripts, bookmarks, raw ideas) | **Immutable** — never edit raw sources (raw idea files are the one exception: see §12) |
| `wiki/` | LLM-generated knowledge base (also an Obsidian vault) | **Mutable** — this is where you work |
| `AGENTS.md` | This file — tells agents how to operate | **Propose changes** — never edit unilaterally |

### Directory Structure

```
llm-wiki/
├── AGENTS.md                  # THIS FILE — agent operating manual
├── CLAUDE.md                  # Points Claude Code to this file
├── raw/                       # Immutable source material
│   ├── papers/                # Academic papers, whitepapers
│   ├── articles/              # Blog posts, web articles
│   ├── notes/                 # Personal notes, meeting notes
│   ├── transcripts/           # Video/podcast transcripts
│   ├── bookmarks/             # Saved links with context
│   ├── ideas/                 # Raw ideas and their grill transcripts (§12)
│   └── assets/                # Images extracted from sources
├── wiki/                      # LLM-generated knowledge base (Obsidian vault)
│   ├── index.md               # Master catalog of all wiki pages
│   ├── log.md                 # Activity log (ingest, query, lint)
│   ├── GLOSSARY.md            # Shared vocabulary (§11)
│   ├── .templates/            # Page and Spec templates
│   ├── assets/                # Wiki-specific images
│   ├── research/              # Learning & investigating
│   │   ├── sources/
│   │   ├── entities/
│   │   ├── concepts/
│   │   ├── comparisons/
│   │   └── synthesis/
│   ├── projects/              # Building
│   │   ├── hubs/              # One page per live project (§12)
│   │   ├── sources/           # Specs live here
│   │   ├── entities/
│   │   ├── concepts/
│   │   ├── comparisons/
│   │   └── synthesis/
│   ├── content/               # Creating & publishing
│   │   ├── sources/
│   │   ├── entities/
│   │   ├── concepts/
│   │   ├── comparisons/
│   │   └── synthesis/
│   └── personal/              # You and your life
│       ├── sources/
│       ├── entities/
│       ├── concepts/
│       ├── comparisons/
│       └── synthesis/
└── archive/                   # Done Specs and their raw ideas (not indexed)
    ├── specs/
    └── raw-ideas/
```

### Key Files

- **`wiki/index.md`** — Master catalog. Every wiki page gets an entry here. The table of contents for the entire brain.
- **`wiki/log.md`** — Chronological activity log. Every ingest, query filing, and lint gets recorded. Your audit trail.
- **`wiki/GLOSSARY.md`** — Shared vocabulary for every agent that works with the wiki.
- **`AGENTS.md`** — You're reading it. The source of truth for how agents operate.

**Example:** the Open Loops repo has a tiny example wiki in `modules/wiki/example/` ([open it](../example/wiki/index.md) when you read this file in that repo): one hub, one entity, a glossary, an index and a log. Read it to see the shape of each file.

---

## 2. Session Protocol

Every new conversation **MUST** begin with these steps, in order:

1. **`git pull`** — Sync latest changes from other devices or agents (skip if the wiki has no remote).
2. **`qmd update`** — Re-index any new or changed files so search is current (skip if qmd is not installed; see §7).
3. **Read `wiki/GLOSSARY.md`** — Load the shared vocabulary (§11).
4. **Read last 5 entries of `log.md`** — Understand what happened recently. Context matters.
5. **Proceed** with the Owner's request.

This takes 30 seconds and prevents you from duplicating work, missing context, or clobbering changes. Never skip it.

---

## 3. Wiki Structure

The wiki has 4 sections — the "rooms" of the memory palace. Each serves a distinct purpose:

| Section | What lives here | Mental model |
|---------|----------------|--------------|
| `research/` | Papers, agentic AI, tech trends, dev tools, dotfiles, productivity | Things you're **learning & investigating** |
| `projects/` | Work projects, side projects — goals, decisions, design docs, blockers, Specs | Things you're **building** |
| `content/` | Videos, posts, talks: ideas, scripts, prompt templates, content calendar | Things you're **creating & publishing** |
| `personal/` | Books, movies, health, courses, life goals, journal | Things about **you and your life** |

### Routing Mental Model

When deciding where something goes, ask: **Am I learning? Building? Creating content? Or is this about my life?**

- A paper on transformer architectures → `research/`
- Design decisions for a side project → `projects/`
- A video script idea inspired by that paper → `content/`
- A book you're reading for fun → `personal/`

Sometimes the answer isn't obvious. Use your judgment — the sections are guides, not walls.

### Subcategories

Subcategories within sections (e.g., `personal/books/`, `personal/movies/`, `personal/health/`, `personal/courses/`) emerge organically as content arrives. Don't pre-create empty directories. When a section accumulates enough pages of a kind, propose organizing them into a subdirectory.

### Cross-Referencing

Content often spans sections. A research paper might inspire a video idea. A project might use a tool you researched.

- Add `[[wikilinks]]` in **both directions**. If A links to B, B should link back to A.
- A research paper that inspires a video idea gets linked from both `research/` and `content/`.
- Use the `related:` frontmatter field for explicit cross-section connections.

---

## 4. Page Types

Five page types are available. Think of them as tools in a toolkit — use the right one for the job, don't force every ingest through all five.

### Source Summary

A distillation of a single raw source. Created so the original never needs re-reading.

- **When:** Every ingest creates one.
- **Include:** Key findings, methodology (if applicable), relevance to existing wiki content, notable quotes.
- **Location:** `<section>/sources/<descriptive-name>.md`

```yaml
---
title: "Attention Is All You Need"
type: source-summary
section: research
tags: [transformers, attention, architecture]
sources:
  - raw/papers/vaswani-2017-attention.pdf
created: 2026-04-14
updated: 2026-04-14
related:
  - "[[transformer-architecture]]"
  - "[[self-attention]]"
---
```

### Entity Page

A specific thing: person, tool, framework, company, book, concept library, etc. Gets richer as more sources mention it.

- **When:** An entity appears in 2+ sources, or is central to a single important source.
- **Include:** What it is, how different sources describe it, evolution over time, relationships to other entities.
- **Location:** `<section>/entities/<name>.md`

```yaml
---
title: "PyTorch"
type: entity
section: research
tags: [framework, deep-learning, python]
sources:
  - raw/papers/paszke-2019-pytorch.pdf
  - raw/articles/pytorch-2-release.md
created: 2026-04-14
updated: 2026-04-14
related:
  - "[[jax]]"
  - "[[deep-learning-frameworks]]"
---
```

### Concept Page

An abstract idea or theme that cuts across multiple sources. Where entity pages are about *things*, concept pages are about *ideas*.

- **When:** A concept appears across multiple sources with different perspectives.
- **Include:** Definition, different perspectives from sources, agreements/contradictions, open questions.
- **Location:** `<section>/concepts/<name>.md`

```yaml
---
title: "Scaling Laws"
type: concept
section: research
tags: [scaling, training, compute]
sources:
  - raw/papers/kaplan-2020-scaling-laws.pdf
  - raw/papers/hoffmann-2022-chinchilla.pdf
created: 2026-04-14
updated: 2026-04-14
related:
  - "[[chinchilla]]"
  - "[[compute-optimal-training]]"
---
```

### Comparison Page

Side-by-side analysis. Often born from an Owner query worth preserving.

- **When:** The Owner asks a comparison question and the answer is worth keeping.
- **Include:** Criteria, comparison table, analysis, recommendation if applicable.
- **Location:** `<section>/comparisons/<name>.md`

```yaml
---
title: "PyTorch vs JAX"
type: comparison
section: research
tags: [framework, comparison, deep-learning]
sources:
  - raw/articles/pytorch-2-release.md
  - raw/articles/jax-overview.md
created: 2026-04-14
updated: 2026-04-14
related:
  - "[[pytorch]]"
  - "[[jax]]"
---
```

### Synthesis Page

High-level narrative tying together entities, concepts, and sources into a coherent thesis or overview. The most valuable page type — it's where insight lives.

- **When:** Enough material exists to form a coherent thesis or overview.
- **Include:** Narrative, key arguments, supporting evidence from wiki pages, evolving thesis.
- **Location:** `<section>/synthesis/<name>.md`

```yaml
---
title: "The State of LLM Agents in 2026"
type: synthesis
section: research
tags: [agents, llm, overview]
sources:
  - raw/papers/agent-survey-2026.pdf
  - raw/articles/agents-sdk-overview.md
  - raw/articles/tool-use-guide.md
created: 2026-04-14
updated: 2026-04-14
related:
  - "[[tool-use]]"
  - "[[agent-architectures]]"
  - "[[content/ideas/agents-video-series]]"
---
```

### Templates

Page templates live in `wiki/.templates/`. Each template shows the expected structure — headings, sections, and guidance comments — for its page type.

| Template | File |
|----------|------|
| Source Summary | `wiki/.templates/source-summary.md` |
| Entity | `wiki/.templates/entity.md` |
| Concept | `wiki/.templates/concept.md` |
| Comparison | `wiki/.templates/comparison.md` |
| Synthesis | `wiki/.templates/synthesis.md` |
| Build Spec | `wiki/.templates/build-spec.md` (see §12) |
| Exploration Spec | `wiki/.templates/exploration-spec.md` (see §12) |

**How to use templates:**
- When creating a new wiki page, **read the corresponding template first** to understand the expected structure.
- Use the template as a starting point — copy its structure, fill in the content, remove guidance comments.
- **Adapt, don't follow blindly.** Not every section in a template will apply to every page. Omit sections that don't make sense for the specific content. Add sections the template doesn't have if the content calls for it.
- The templates define the *shape* of a page, not a rigid form. Quality and clarity matter more than matching the template exactly.

---

## 5. Frontmatter Convention

Every wiki page must have YAML frontmatter. This powers Obsidian's graph view, search, and the agent's ability to understand the wiki programmatically.

```yaml
---
title: "Page Title"
type: source-summary  # source-summary | entity | concept | comparison | synthesis
section: research     # research | projects | content | personal
tags: [tag1, tag2]    # freeform, lowercase
sources:              # raw source references (for provenance)
  - raw/papers/example.md
created: 2026-04-14   # ISO date
updated: 2026-04-14   # ISO date, refresh on every edit
related:              # explicit cross-section links
  - "[[other-page]]"
---
```

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes | Human-readable title |
| `type` | Yes | One of the 5 page types (a hub uses `type: hub`, see §12) |
| `section` | Yes | Which room of the memory palace |
| `tags` | Yes | Freeform, lowercase, for discoverability |
| `sources` | No | Paths to raw sources. Omit if not source-derived |
| `created` | Yes | ISO date, set once |
| `updated` | Yes | ISO date, **refresh on every edit** |
| `related` | No | Explicit cross-references as wikilinks |

Specs add their own fields (`tracker_id`, `report`, `workspace`, `branch`, `depends_on`, `spec_status`, and `agent` for an Exploration Spec). Their templates name them.

---

## 6. Workflows

### 6a. Ingest (Interactive — Default)

The standard workflow when the Owner drops a source and asks you to process it. Collaborative by design — discuss before executing.

1. The Owner drops a source into `raw/` and asks the agent to ingest.
2. If PDF: convert it to Markdown first, with any PDF-to-Markdown tool the Owner has. Save the Markdown next to the PDF.
3. Read the source content fully.
4. Search the wiki (`qmd search`, or `grep`; see §7) for related existing content.
5. **Discuss with the Owner:**
   - Key takeaways from the source
   - Proposed section placement (with reasoning)
   - Which existing pages would be updated
   - Whether new entity/concept pages are warranted
6. **Wait for the Owner's approval or adjustments.**
7. Execute:
   a. Create source summary page with frontmatter
   b. Update or create entity pages for key entities
   c. Update or create concept pages for key ideas
   d. Add `[[wikilinks]]` in all affected pages (bidirectional)
   e. Update `index.md` with new entries
   f. Append ingest entry to `log.md`
   g. Run `qmd update` to re-index (if qmd is installed)

### 6b. Ingest (Batch — On Explicit Request)

For processing multiple sources with less supervision. Only use when the Owner explicitly asks for batch mode.

For each source:
1. Read the source
2. Determine section placement
3. Create source summary
4. Update or create entity/concept pages as warranted
5. Add cross-references
6. Update `index.md` and `log.md`

When done, provide a summary of all changes: pages created, pages updated, cross-references added. Run `qmd update` once at the end (if qmd is installed).

### 6c. Query

When the Owner asks a question about wiki contents.

1. The Owner asks a question.
2. Read `index.md` for an overview of available content.
3. Search via `qmd search "<keywords>"` for relevant pages (fall back to `qmd vsearch` if no hits; without qmd, use `grep`).
4. Read the top relevant pages in full.
5. Synthesize an answer citing specific wiki pages with `[[wikilinks]]`.
6. Note if information is incomplete or contradictory.
7. Ask: *"Want me to file this as a wiki page?"* — only if the answer seems reusable.
8. Only file back into the wiki with the Owner's explicit approval.

### 6d. Lint

A health check for the wiki. Run when the Owner asks, or suggest it periodically.

Lint is a natural fit for a **fan-out of subagents** (or a workflow, if your agent has one): six independent read-only dimensions over many pages. Doing all six inline in a single context loses issues to drift and laziness on long lists.

#### Fan-out shape (full lint)

Run three phases:

1. **Find (parallel)** — one subagent per dimension, all scoped to the same wiki paths. Each returns a structured list `[{page, line, type, evidence, suggested_fix}]`:
   - Contradictions between pages
   - Stale claims superseded by newer sources
   - Orphan pages with no inbound `[[wikilinks]]`
   - Missing pages — concepts referenced but never written
   - Missing cross-references between related pages
   - Data gaps fillable by new sources
2. **Verify (parallel, per finding)** — a skeptic subagent reads each finding and tries to refute it. Defaults to `refuted=true` when uncertain. Drops false positives before the Owner sees them.
3. **Synthesize (inline)** — the main session dedupes by `(page, type)`, groups by dimension, and prints the report.

Then present to the Owner, get approval per fix, and apply fixes **inline** (not in the subagents).

#### When NOT to fan out

- Single dimension only ("find orphans"): one search + read is faster.
- Scope is one page or a handful of just-touched pages.
- The Owner wants a quick sanity check, not a full audit.
- Your agent cannot run subagents.

Trigger rule: ≥2 dimensions × scope large enough that inline reading would crowd context. Otherwise lint inline.

#### Hard rules

- **Never write from inside the subagents.** No file edits, no `log.md` appends, no `[[wikilink]]` insertions. Subagents fan out *judgments*; the main session sequences *writes*.
- **Each fix needs the Owner's approval before applying.** Don't batch-approve.

#### Steps

1. The Owner asks to lint the wiki (or a scope).
2. If scope qualifies (see trigger rule): run the fan-out above. Otherwise: lint inline.
3. Report findings grouped by dimension with specific suggestions.
4. Offer to fix each issue (with the Owner's approval).
5. Apply approved fixes inline.
6. Append lint entry to `log.md`.

---

## 7. Tools

### qmd (Search, optional)

[qmd](https://github.com/tobi/qmd) is the recommended tool for searching and managing the wiki index. It is optional: without it, search with `grep -rn` (or `rg`) over `wiki/`, and skip every `qmd update` step.

```bash
qmd search "keyword"               # Fast BM25 keyword search (default)
qmd vsearch "semantic query"       # Vector semantic search (fallback)
qmd get "wiki/research/page.md"    # Retrieve full document
qmd update                         # Re-index after changes
qmd update --pull                  # Git pull + re-index
qmd status                         # Index health and collection info
```

**When to use which:**
- `search` — Default. Instant BM25 keyword search. Use specific terms (entity names, glossary words, distinctive phrases).
- `vsearch` — Fallback when keyword search returns nothing or the query is conceptual (e.g., "papers about making models smaller"). Slower (~5-10s) but tolerates paraphrasing.
- `qmd query` (hybrid LLM re-ranking) is not used by default — it is too slow on CPU (1-3 min/query) and needs heavy models.

**Without qmd:**
```bash
grep -rli "keyword" wiki/          # Pages that mention a term
grep -rn "\[\[page-name" wiki/     # Inbound links to a page
```

**MCP server** (for agents that support Model Context Protocol):
```json
{"mcpServers": {"qmd": {"command": "qmd", "args": ["mcp"]}}}
```
Exposes tools: `query`, `get`, `multi_get`, `status`.

### git

Standard git for version control. Key rules:

- **NEVER commit automatically.** Only commit when the Owner explicitly asks.
- Use descriptive commit messages following this pattern:
  - `ingest: <source title>`
  - `query: filed <page title>`
  - `lint: fixed orphans and cross-refs`
  - `update: refreshed <page title> with new source`

### Dataview (Obsidian Plugin)

Dataview can be installed in the `wiki/` vault. It runs live queries over page frontmatter, so the structured YAML you already write (type, section, tags, sources, created, updated) is queryable.

Use Dataview code blocks in wiki pages to create dynamic tables and lists. Examples:

**All concept pages in research, sorted by last updated:**
````markdown
```dataview
TABLE tags, updated
FROM "research/concepts"
WHERE type = "concept"
SORT updated DESC
```
````

**Pages tagged "transformers":**
````markdown
```dataview
LIST
WHERE contains(tags, "transformers")
SORT title ASC
```
````

**Source summaries created in the last 30 days:**
````markdown
```dataview
TABLE title, section, created
WHERE type = "source-summary" AND created >= date(today) - dur(30 days)
SORT created DESC
```
````

**When to use Dataview:**
- In `index.md` or section READMEs to auto-generate page listings instead of maintaining them manually.
- In synthesis pages to pull together all sources on a topic dynamically.
- When the Owner asks for an overview or inventory of wiki content.

**When NOT to use Dataview:**
- Don't replace simple `[[wikilinks]]` with Dataview queries. Links are for narrative connections; Dataview is for structured overviews.
- Don't use Dataview in source summaries — those should be static distillations.

### MkDocs (web UI, optional)

`mkdocs.yml` serves `wiki/` as a website (`pip install mkdocs-material mkdocs-obsidian-bridge mkdocs-callouts`, then `mkdocs serve`).

---

## 8. Conventions

### Linking

- Always use `[[wikilinks]]` (Obsidian-style) for internal wiki pages. Never standard markdown links.
- Links should be **bidirectional** — if A links to B, B should link back to A when relevant.
- Use `[[page-name|Display Text]]` when the display text differs from the page name.
- External URLs use standard markdown: `[text](https://...)`.

### File Naming

- Lowercase, hyphens for spaces: `scaling-laws.md`, `chain-of-thought.md`
- Names should read naturally as wikilinks: `[[scaling-laws]]` should make sense in a sentence.
- Source summaries follow `<author>-<year>-<short-title>.md` when applicable (e.g., `vaswani-2017-attention.md`).
- Entity/concept pages use the most common name: `pytorch.md` not `pytorch-framework.md`.

### Images

| Type | Location | Reference syntax |
|------|----------|-----------------|
| Source images (extracted from raw) | `raw/assets/` | `![[image-name.png]]` |
| Wiki images (created for wiki pages) | `wiki/assets/` | `![[image-name.png]]` |

### Log Format

Every operation gets logged in `wiki/log.md`:

```
## [2026-04-14] ingest | Attention Is All You Need
- Created source summary: research/sources/vaswani-2017-attention.md
- Created entity page: research/entities/transformer-architecture.md
- Updated concept page: research/concepts/self-attention.md
- Added cross-references to 3 existing pages
```

| Field | Format |
|-------|--------|
| Date | `[YYYY-MM-DD]` |
| Operation | `ingest`, `query`, `lint`, `init`, `update` |
| Title | Brief description of what was processed |
| Details | Bullet list of specific changes |

Parseable: `grep "^## \[" wiki/log.md | tail -5`

---

## 9. Evolution

The wiki is a brain — let it grow organically.

- **Look before you leap.** Before creating a new page, search the wiki and browse `index.md` to check if a relevant page already exists. Duplicate pages are the enemy.
- **Respect existing patterns.** Before establishing a new convention, check how similar situations were handled before. Consistency matters more than perfection.
- **Propose, don't impose.** If you think `AGENTS.md` should be updated (new convention, workflow improvement, tool addition), propose the change to the Owner. Don't edit this file unilaterally.
- **New sections on request.** The 4-section structure can expand when the Owner needs it. Scaffold the directory and add a README explaining the section's purpose.
- **Subcategories emerge.** Don't pre-create `personal/books/` on day one. When there are enough book pages that organization helps, propose the restructure.
- **The routing mental model may evolve.** That's fine. When it does, update this file to reflect the new thinking.
- **Tags are freeform.** Don't over-systematize them. Let patterns emerge, then consolidate if needed.

---

## 10. Quick Reference

### Session Startup

```
1. git pull                          (if the wiki has a remote)
2. qmd update                        (if qmd is installed)
3. read wiki/GLOSSARY.md
4. grep "^## \[" wiki/log.md | tail -5
5. Proceed with the Owner's request
```

### Frontmatter Template

```yaml
---
title: ""
type:       # source-summary | entity | concept | comparison | synthesis
section:    # research | projects | content | personal
tags: []
sources:
  - raw/
created: YYYY-MM-DD
updated: YYYY-MM-DD
related:
  - "[[]]"
---
```

### Common Search Commands

```bash
qmd search "exact keyword"              # Fast keyword search (default)
qmd vsearch "conceptual question"       # Semantic search (fallback)
qmd get "wiki/path/to/page.md"          # Retrieve full page
qmd update                              # Re-index after changes
qmd status                              # Check index health
grep -rli "exact keyword" wiki/         # Without qmd
```

### Log Entry Format

```
## [YYYY-MM-DD] operation | Title
- Detail line 1
- Detail line 2
```

### File Naming Examples

| Type | Example |
|------|---------|
| Source summary | `vaswani-2017-attention.md` |
| Entity page | `pytorch.md` |
| Concept page | `scaling-laws.md` |
| Comparison | `pytorch-vs-jax.md` |
| Synthesis | `state-of-llm-agents-2026.md` |

### Ingest Checklist

```
□ Source in raw/?
□ PDF converted? (if applicable)
□ Read source fully
□ Search the wiki for related content
□ Discuss plan with the Owner
□ Owner approved?
□ Read template from wiki/.templates/ for the page type
□ Create source summary
□ Update/create entity pages
□ Update/create concept pages
□ Add bidirectional [[wikilinks]]
□ Update index.md
□ Append to log.md
□ qmd update (if installed)
```

### Query Checklist

```
□ Read index.md
□ Search the wiki for relevant pages
□ Read top results in full
□ Synthesize answer with [[wikilinks]]
□ Note gaps or contradictions
□ Offer to file as wiki page (if reusable)
□ File only with the Owner's approval
```

### Lint Checklist

```
□ Check for contradictions
□ Check for stale claims
□ Find orphan pages
□ Find missing pages (mentioned but not created)
□ Find missing cross-references
□ Identify data gaps
□ Report findings grouped by type
□ Fix with the Owner's approval
□ Append to log.md
```

---

## 11. Shared Vocabulary (GLOSSARY.md)

The file `wiki/GLOSSARY.md` is the **shared vocabulary** for all agents working with this wiki. It defines canonical terms, avoids synonyms, and resolves ambiguities.

### Rules

1. **Read GLOSSARY.md at session start** — before any ingest or query, load the glossary.
2. **Challenge language** — if the Owner uses a term that conflicts with GLOSSARY.md, call it out immediately.
3. **Update inline** — when a term is resolved during a grill session or ingest, update GLOSSARY.md immediately.
4. **One sentence max** per definition — what it IS, not what it does.
5. **Be opinionated** — pick one canonical term, list alternatives under `_Avoid_`.
6. **Only domain-specific terms** — no general programming concepts.
7. **Flag conflicts** — if a term is used ambiguously, add to "Flagged ambiguities" and resolve.

### When to add terms

- During a **Grill Session** when a term is resolved
- During **Ingest** when a new domain concept appears
- When the Owner corrects terminology usage

---

## 12. Idea Forge Pipeline

The wiki is the central brain of the Idea Forge system — a pipeline for turning raw thoughts into executed work. Open Loops runs the execute stage. The capture and refine stages match the Open Loops `capture` and `refine` modules (`modules/capture/`, `modules/refine/`), if the Owner installed them.

### Stage 1: Capture

Raw ideas land in `raw/ideas/` as freeform markdown. Filename: `YYYY-MM-DD-<slug>.md`. No template required. Do not place any non-idea files (READMEs, etc.) in this folder.

Entry points:
- A chat message to an always-on agent of the Owner (for example a KiroCrew or OpenClaw agent) → the agent writes to `raw/ideas/`
- A coding-agent session → the Owner or the agent writes to `raw/ideas/`
- Direct file creation

### Stage 2: Refine

Use the appropriate **grill skill** to refine a raw idea into a Spec:
- **spec-task** — for Build Specs (spec-driven decomposition: scope, task breakdown, boundaries, verification, plus domain model sharpening)
- **spec-exploration** — for Exploration Specs (autonomous research, experiments, iterative optimization). This skill probes for execution environment, metrics, run commands, constraints, and everything the Exploration Worker (the `auto-researcher` agent) needs to run without the Owner.

Steps:
1. Read the raw idea from `raw/ideas/`
2. Search the wiki for related existing content
3. Run the grill session — append each Q&A (question, answer, decision) to the raw idea file as the conversation progresses
4. Update `wiki/GLOSSARY.md` inline when new terms are resolved
5. The raw idea file becomes the full transcript and source of truth
6. Write the complete Spec at `wiki/projects/sources/<name>.md` using the appropriate template. **The Spec must be self-contained** — any agent or person reading it cold should have full context to execute without referring back to the raw idea file. The raw file is the transcript; the Spec is the authoritative reference.
7. Update `wiki/index.md` with the new Spec
8. Log to `wiki/log.md`
9. Ask: "Should I create a Tracker Task for this?" (never auto-create)
10. Add the Spec to the "Specs" list of its hub in `wiki/projects/hubs/` (create a hub only if the project is new and live)

### Hubs, Specs and the archive

- **Hub** (`wiki/projects/hubs/<project>.md`): one page per live project. Frontmatter: `type: hub` and a `status` (for example `active`). It holds intent, dated current state, canonical links (repo, Tracker, reports, design docs), one-line decisions with reasons, open questions, and a list of archived Specs.
- **Content rule:** the wiki is a map, not a store of results. Do not copy metric values, file:line references, function signatures, YAML or model names into hubs or entity pages. The code, the configs and the linked docs are the source of truth. Keep a number only if no other location has it and it is useful for the long run.
- **Trust rule:** do not trust a number in the wiki. Follow the link and read the source.
- **Spec end:** when the work for a Spec is Done, move the Spec and its raw idea to `archive/specs/` and `archive/raw-ideas/`, add one outcome line with links to the hub, and update `wiki/index.md`. Search does not index `archive/` (with qmd, do not add it as a collection).

### Stage 3: Track

**Single-Spec idea (default):** When the Owner confirms, create a Tracker Task with:
- Title matching the Spec page title
- Body: 2-3 sentence summary + a `Spec:` line with the absolute path of the wiki Spec page (`Spec: <wiki>/wiki/projects/sources/<name>.md`)
- The wiki Spec page gets the Tracker's id for the Task in its `tracker_id:` frontmatter field

**Multi-Spec idea (split via spec-task's Split Checkpoint):** When the Owner confirms the whole set of pieces at once (one confirmation covers all pieces — do not ask per piece), create:
- One **parent** Task representing the overall effort.
- One **child** Task per piece, in the order and dependencies decided at the checkpoint. Every piece gets a child Task immediately, including deferred ones — a deferred child's body says `Spec: <path> (deferred — waiting on <earlier piece name>)`.
- Dependencies between child Tasks matching each Spec's `depends_on` frontmatter (child B depends on child A if B's Spec has `depends_on: ["spec-a"]`), in the way the Owner's `tracker.md` describes.
- Each Spec's `tracker_id:` field gets its own child Task's id (not the parent's).

### Stage 4: Execute (Open Loops)

Specs are executed autonomously by Open Loops: an Orchestrator that the Host starts on a schedule reads the Tracker each Cycle and spawns a coding-agent Worker for each Ready Task, each in its own Workspace (a git worktree on a branch `ol-<slug>`).

**Trigger:** the Owner moves the Task to Ready.

**For Build Specs:**
- The Orchestrator spawns a Worker in a Workspace (`ol-<slug>`)
- The Worker reads the Spec, executes, and opens a PR
- On completion: the Worker comments on the Task and moves it to In Review; the Task is Done when the PR is merged or closed

**For Exploration Specs:**
- The Orchestrator spawns the Worker with the agent in the Spec's `agent:` field (`auto-researcher`)
- The Worker reads the Spec, extracts all setup parameters (metric, run command, scope, budget)
- Runs the Karpathy-style experiment loop: modify → run → measure → keep or revert → repeat
- Experiment state (`results.tsv`, notes) lives in `<workspace>/.openloops/<slug>/`, where `<workspace>` is the Spec's `workspace:` field (the project repo, NOT the Worker's worktree) — it survives git resets and worktree deletion
- On completion: writes the findings to the report file named in the Spec's `report:` field, links it from the wiki Spec, and moves the Task to In Review

**Key principle:** the Spec must be complete enough that the Worker never needs to ask a question. All information required for autonomous execution comes from the Spec. The raw idea file is available for additional context but should not be required.

Any agent can also pick up a Spec manually:
1. Read the Spec page from the wiki
2. Read linked wiki pages for additional context
3. Read `wiki/GLOSSARY.md` for vocabulary
4. If report links exist, read those for detailed results and context
5. Ask relevant new questions if needed — it's fine to ask as long as they aren't already answered in the Spec
6. Execute the work
7. On completion: update the Spec's Status checklist, write results back (a summary in the wiki, extensive results in a report file with a link back), and update the Task in the Tracker

### Spec Types

Two templates in `wiki/.templates/` (copies of the Open Loops `core/templates/`):

| Template | When | Key fields |
|----------|------|------------|
| `build-spec.md` | Clear deliverable, known approach | What, Why, Approach, Acceptance Criteria |
| `exploration-spec.md` | Open-ended research | Hypothesis, Search Space, Success Metric, Time Budget |

### Reports

Extensive results (experiment tables, plots, long write-ups) go in a report file — a local Markdown or HTML file — not inlined in wiki pages. The wiki page holds:
- Summary of findings
- `report:` field in frontmatter with the report's path
- The agent can read the report when it needs depth
