# Wiki module (optional)

A central LLM wiki: a knowledge base that grows over time across all of the Owner's projects, so that the Owner does not give the same context again and again to related projects. Specs, decisions, glossary terms, hubs and results written back after Done live here.

Open Loops never needs the wiki. The core works with only a Tracker, with the Spec in the Task body or in a file in the project repo. The wiki is the optional addition: a Task's `Spec:` line can point to a Spec page in the wiki.

Setup asks one yes/no question for this module (step 5 of [`SETUP.md`](../../SETUP.md)). Default: no.

## What is here

| Path | What it is |
|---|---|
| [`scaffold/`](scaffold/) | The files that setup copies into a new wiki directory. |
| [`scaffold/AGENTS.md`](scaffold/AGENTS.md) | The operating manual for any agent that works on the wiki: session protocol, structure, page types, frontmatter, the ingest, query and lint workflows, tools, conventions, glossary rules and the Idea Forge pipeline (capture, refine, track, execute). `scaffold/CLAUDE.md` points Claude Code to it. |
| [`scaffold/wiki/.templates/`](scaffold/wiki/.templates/) | Page templates: source summary, entity, concept, comparison, synthesis. Setup adds the two Spec templates from [`core/templates/`](../../core/templates/). |
| `scaffold/wiki/{index,log,GLOSSARY}.md` | An empty index, log and glossary to start from. |
| `scaffold/{package.json,mkdocs.yml,mise.toml,.gitignore}` | Optional tooling: qmd search (`package.json`), a MkDocs web view, the Node version for `mise`, and the files git ignores. |
| [`example/`](example/wiki/index.md) | A tiny neutral example wiki: one hub, one entity, a glossary, an index and a log. Not copied by setup. |

## How it fits Open Loops

- **Specs in the wiki.** A Spec is a page in `<wiki>/wiki/projects/sources/<name>.md`, made from `wiki/.templates/build-spec.md` or `exploration-spec.md`. The Task's `Spec:` line holds the page's absolute path: `Spec: <wiki>/wiki/projects/sources/<name>.md`. The Workers can read and update it because setup adds the wiki directory to `{{EXTRA_DIRS}}` in `runtime.md`.
- **Results written back.** When a Worker finishes, it updates the Spec's Status checklist (Worker rules, On Completion). After Done, an agent session that follows `AGENTS.md` moves the Spec to `archive/` and adds one outcome line to the project's hub.
- **Hubs.** One page per live project in `wiki/projects/hubs/`: intent, current state, links, decisions, open questions, and its Specs.

## Search (optional)

[qmd](https://github.com/tobi/qmd) gives fast local search over the wiki (`qmd search`, `qmd vsearch`). It is optional: without it, the manual tells the agent to use `grep`. Install it from its own docs, for example `npm install -g @tobilu/qmd`, then index the wiki once:

```sh
cd <wiki>
qmd collection add wiki --name wiki
qmd collection add raw --name raw-sources
qmd embed
```

## Credits

The wiki follows [Andrej Karpathy's "LLM Wiki" pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): an LLM agent keeps a persistent, interlinked Markdown wiki from raw sources, instead of re-deriving answers from raw chunks each time. The manual and the templates in this module are Open Loops' own text. qmd is a separate project by Tobi Lutke (MIT), credited in [`NOTICE`](../../NOTICE); it is not part of this repository.
