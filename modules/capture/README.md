# Capture module

Optional. Rules for the Owner's coding agent: keep each idea in its own raw idea file, append the grill transcript to it, and turn it into a self-contained Spec that a Worker can run.

| File | What it is |
|---|---|
| [`capture.md`](capture.md) | The instructions file. Setup copies it to `<home>/capture.md`, fills its placeholders, and links it from the agent's own instructions file. |

Placeholders:

| Placeholder | Meaning | Default |
|---|---|---|
| `{{IDEAS_DIR}}` | The directory for raw idea files | `<home>/ideas` |
| `{{SPECS_DIR}}` | The directory for finished Specs. The Workers must be able to read it (an `--add-dir` path in `runtime.md`). | `<home>/specs` |

The rules name two skills: `spec-task` and `spec-exploration` from the [refine module](../refine/README.md), and `wayfinder` from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). Setup installs `wayfinder` from upstream; it is not copied into this repo.

Setup asks one yes/no question for this module: see "Optional modules" in [`SETUP.md`](../../SETUP.md).
