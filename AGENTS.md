# Agent instructions for this repo

Read this before you change anything in Open Loops. It is for people and coding agents who contribute. (To set up Open Loops on a machine, follow [`SETUP.md`](SETUP.md) instead.)

## Hard rules

1. **Update `SPEC.md` in the same change as a behavior change.** If you change what the Orchestrator, a Worker or a Slot does, change [`SPEC.md`](SPEC.md) in the same commit. If you change a Slot Contract, change it in both `SPEC.md` and `adapters/<slot>/README.md`. A change that makes the prompts and `SPEC.md` disagree is a bug.
2. **Use the glossary words.** Every term is defined in [`GLOSSARY.md`](GLOSSARY.md). Use those words only, in code, prompts, docs, tests and commit messages: Task (not ticket or issue), PR (not CR or MR), In Review (not Awaiting Review), Worker (not sub-agent), Cycle (not tick or run). A new term goes into `GLOSSARY.md` in the same change, with one sentence and an `_Avoid_` line.
3. **The core names no Slot product.** `core/` says "the Tracker", "the Runtime" and so on, and never names a product, a command of a product, or the Cycle interval. Products live only in `adapters/` and in the Owner's notes files. A test checks this.
4. **Placeholders only.** Files in this repo hold `{{...}}` placeholders, never a real ID, path, login, URL of a private service, or person's alias. Setup writes real values into the Owner's home directory.
5. **No third-party skill files.** Third-party skills are installed from their source and listed in [`third-party.json`](third-party.json). Never copy them into the repo. When the list changes, run `./install-third-party.sh --notice > NOTICE` and replace each credits table with `./install-third-party.sh --credits`.
6. **Keep today's behavior where it works.** Fix a real problem; do not redesign, consolidate or add a feature that no Task asks for.

## Where things are

| To change | Edit | And also |
|---|---|---|
| What a Cycle does | [`core/orchestrator.md`](core/orchestrator.md) | `SPEC.md` (sections 3, 4, 10, 11), a fixture scenario |
| What a Worker does | [`core/worker-rules.md`](core/worker-rules.md) | `SPEC.md` (sections 6, 7) |
| `state.json` | [`core/state.schema.json`](core/state.schema.json) | the State File section of `core/orchestrator.md`, `SPEC.md` section 9 |
| A Slot Contract | `adapters/<slot>/README.md` | `SPEC.md` section 8, the Contract map of each example, `SETUP.md` step 3 |
| An example notes file | `adapters/<slot>/<example>.md` | its rows in the Contract map |
| The setup flow | [`SETUP.md`](SETUP.md) | `tests/cycle_fixture/test_setup.py` |
| A Spec template | [`core/templates/`](core/templates/) | `SPEC.md` section 5, `modules/wiki/` if it copies the template |
| The README first screen | [`README.md`](README.md) | keep install and verify before any long text |

## Style of the docs and prompts

- Short sentences in plain English. One instruction per sentence. Active voice.
- Prompts are instructions for an agent: say what to do, in order, with the exact command where one exists.
- Give paths relative to the repo, or with `<home>`, `<repo>`, `<clone>` and `{{...}}` placeholders.
- Every link in a doc must resolve to a file in the repo.

## Tests

Run the offline checks before each commit. They need no agent:

```sh
python3 -m unittest discover -s tests/cycle_fixture
```

The Cycle fixture runs real Cycles with a real agent and costs tokens. Run it when you change `core/` or an example notes file that it uses (see [`tests/cycle_fixture/README.md`](tests/cycle_fixture/README.md)):

```sh
python3 tests/cycle_fixture/run_fixture.py --scenario build
```

A change to Orchestrator or Worker behavior adds or extends one fixture scenario. A good check looks only at external results (Task files, `state.json`, git branches, the Cycle log, the Notifier log), never at prompt wording or the agent's reasoning text.

## Commits and PRs

- One logical change per commit, with a message that says what changed and why.
- A PR description says what changed, why, how you tested it, and the risk.
- Agent-written PRs follow the same rules. Read the diff yourself before you open the PR.
