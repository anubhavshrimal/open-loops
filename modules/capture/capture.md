# Idea capture

These rules tell you, the Owner's coding agent, how to keep the Owner's ideas until they become Specs. They are part of the Open Loops capture module.

- **One raw idea file per idea.** When the Owner dumps an idea, write it to `{{IDEAS_DIR}}/YYYY-MM-DD-<slug>.md` (today's date and a short slug for the idea).
- **Append the grill transcript.** During a grill session on that idea, append each question and answer to the same raw idea file as the conversation progresses.
- **The raw idea file is the full transcript and the source of truth** for that idea.
- **Refine with a skill.**
  - For a Spec that a Worker will run without a human: use the `spec-task` skill (the Open Loops refine module), or `spec-exploration` for an Exploration Spec.
  - For general domain refinement: use the `wayfinder` skill (from mattpocock/skills). Ideas routinely decompose into more than one Task, so default to wayfinder's map/frontier flow rather than a single-session grill.
- **Write a self-contained Spec.** After refinement, write the complete Spec at `{{SPECS_DIR}}/<name>.md`. It must be self-contained: any agent or person reading it must have full context to execute without referring back to the raw idea file.
