---
title: "Recipe Scaler"
type: hub
status: active
section: projects
tags: [hub, side-project, cli]
sources: []
created: 2026-01-10
updated: 2026-02-02
related:
  - "[[pint]]"
---

# Recipe Scaler

## Intent

A small command-line tool that scales a Base Recipe to any number of servings and converts its units, so that cooking for a group needs no mental arithmetic.

## Current state (2026-02-02)

Scaling works for metric units. Unit conversion between metric and US kitchen units is the next piece of work.

## Links

- Repo: `~/code/recipe-scaler`
- Tracker: the project's Task list
- Reports: `~/code/recipe-scaler/.openloops/` (one folder per Task)

## Decisions

- Store recipes as YAML files, not a database: they are easy to edit by hand and to review in a PR.
- Use [[pint]] for units instead of a hand-written table: it already knows the kitchen units.

## Open questions

- Round "1.3 eggs" up or down? Ask the Owner before the next Spec.

## Specs

- (none live) A new Spec goes in `wiki/projects/sources/<name>.md` and gets a line here.

## Archived Specs

- 2026-01-24 — scale-by-servings: Done; scaling for metric units is merged.
