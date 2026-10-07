# LLM Wiki — Agent Instructions

Read `AGENTS.md` in full before doing anything. It is the operating manual.

## Quick reference
- Shared vocabulary: `wiki/GLOSSARY.md` — read first, update inline when terms are resolved
- Session start: `git pull` → `qmd update` (if installed) → read `wiki/GLOSSARY.md` → read last 5 log entries
- Templates: `wiki/.templates/` (source-summary, entity, concept, comparison, synthesis, build-spec, exploration-spec)
- Index: `wiki/index.md` — update on every page creation
- Log: `wiki/log.md` — append on every operation

## Idea Forge Specs
- Build Specs: clear deliverable → `wiki/.templates/build-spec.md`
- Exploration Specs: open-ended research → `wiki/.templates/exploration-spec.md`
- Both go in `wiki/projects/sources/`, and each belongs to a hub in `wiki/projects/hubs/`
- Done Specs and their raw ideas move to `archive/` (not indexed). See AGENTS.md "Hubs, Specs and the archive"
- The wiki is a map: intent, decisions and links. Facts and numbers live in the code and the linked docs
- Always ask before creating Tracker Tasks
- During grill sessions, append Q&A to the raw idea file in `raw/ideas/` — it becomes the transcript and source of truth
- Specs are distilled from the refined raw idea file
