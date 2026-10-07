# Refine module

Optional. Two skills that interview the Owner until an idea is a Spec that a Worker can run without a human.

| Skill | Use it for |
|---|---|
| [`spec-task`](skills/spec-task/SKILL.md) | A Build Spec. It checks first whether the idea is more than one Task (the split checkpoint: one Spec and one child Task for each piece, with deferred Specs for pieces that wait on others), then decomposes it: scope, task breakdown, boundaries, verification, prior decisions. |
| [`spec-exploration`](skills/spec-exploration/SKILL.md) | An Exploration Spec for the auto-researcher agent: context, objective and seed ideas, execution environment, evaluation, constraints, freedom, risks, handoff. |

Setup copies the two skill folders into the agent's skills directory and replaces `{{CORE_DIR}}` (the `core/` directory of the Open Loops clone, where the Spec templates are).

## Credits

Parts of both skills are derived from [mattpocock/skills](https://github.com/mattpocock/skills), Copyright (c) 2026 Matt Pocock, MIT License. Each `SKILL.md` has an attribution header that names the derived parts and holds the MIT notice.

The skills use the glossary and ADR formats of the `domain-modeling` skill from mattpocock/skills. Those format files are not copied into this repo: setup installs `domain-modeling` from upstream.

Setup asks one yes/no question for this module: see "Optional modules" in [`SETUP.md`](../../SETUP.md).
