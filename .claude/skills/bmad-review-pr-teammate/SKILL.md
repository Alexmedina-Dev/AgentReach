---
name: bmad-review-pr-teammate
description: 'Review a teammate''s pull request as the assigned reviewer, walking .github/Reviewer_template.md section by section against the real diff and optionally posting the result as a real GitHub PR review. Use when the user says "revisa el PR #<n>", "me asignaron reviewer de este PR", "haz de reviewer en este PR", or pastes a PR link/number to review. NOT for reviewing your own just-finished story before opening a PR — for that use bmad-code-review.'
---

# Review PR as Teammate's Reviewer

**Goal:** Act as the human-assigned reviewer on a pull request someone else opened, applying the team's `.github/Reviewer_template.md` checklist exactly — same vocabulary, same verdict — and optionally publish it as a real GitHub PR review.

**Your Role:** You are the reviewer named on this PR, not its author. You did not write this code and have no stake in defending it. Read the linked story/spec if there is one, walk the checklist item by item against the actual diff, and say plainly where it falls short. No rubber-stamping.

**How this differs from `bmad-code-review`:** That workflow is self-review before *you* open a PR for your own story — adversarial layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor) against your own spec. This workflow is the opposite seat: reviewing *someone else's* already-opened PR, from the team's PR-reviewer checklist, ending in an actual GitHub review submission.

## Conventions

- Bare paths (e.g. `checklist.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

**If the script fails**, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying the same structural merge rules as the resolver:

1. `{skill-root}/customize.toml` — defaults
2. `{project-root}/_bmad/custom/{skill-name}.toml` — team overrides
3. `{project-root}/_bmad/custom/{skill-name}.user.toml` — personal overrides

Any missing file is skipped. Scalars override, tables deep-merge, arrays of tables keyed by `code` or `id` replace matching entries and append new entries, and all other arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context you carry for the rest of the workflow run. Entries prefixed `file:` are paths or globs under `{project-root}` — load the referenced contents as facts. All other entries are facts verbatim.

### Step 4: Load Config

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `project_name`, `user_name`, `communication_language`
- `checklist_template` = `{workflow.checklist_template}` (resolves to `{project-root}/.github/Reviewer_template.md` by default)
- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`

If the file at `{checklist_template}` does not exist, HALT and tell the user this skill has nothing to review against — either restore the file or point the workflow at a different one via `bmad-customize`.

### Step 5: Execute Append Steps

Execute each entry in `{workflow.activation_steps_append}` in order.

Activation is complete. If `activation_steps_prepend` or `activation_steps_append` were non-empty, confirm every entry was executed in order before proceeding. Do not begin the main workflow until all activation steps have been completed.

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for disciplined execution:

- **Micro-file Design**: Each step is self-contained and followed exactly
- **Just-In-Time Loading**: Only load the current step file
- **Sequential Enforcement**: Complete steps in order, no skipping
- **State Tracking**: Persist progress via in-memory variables

### Step Processing Rules

1. **READ COMPLETELY**: Read the entire step file before acting
2. **FOLLOW SEQUENCE**: Execute sections in order
3. **WAIT FOR INPUT**: Halt at checkpoints and wait for human
4. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules (NO EXCEPTIONS)

- **NEVER** load multiple step files simultaneously
- **NEVER** skip steps or optimize the sequence
- **NEVER** publish anything to GitHub without an explicit, freshly-given confirmation in this run
- **ALWAYS** read entire step file before execution
- **ALWAYS** follow the exact instructions in the step file
- **ALWAYS** halt at checkpoints and wait for human input

## FIRST STEP

Read fully and follow: `./steps/step-01-resolve-pr.md`
