---
name: bmad-create-pr
description: 'Open (or update) the pull request for the current branch, filling .github/pull_request_template.md from the story file, the code-review findings and real verification evidence. Use when the user says "abre el PR de este story", "crea el pull request", "sube el PR", "abre un draft PR", or asks for a PR at any point of the dev loop. NOT for reviewing a teammate''s PR — that is bmad-review-pr-teammate. NOT for reviewing your own code — that is bmad-code-review.'
---

# Create PR for the Current Branch

**Goal:** Open the pull request for the work on the current branch — or update the one already open — with a body that follows `.github/pull_request_template.md` exactly, grounded in the story file, the code-review findings recorded there, and verification evidence produced in *this* run.

**Your Role:** You are the author of this change, preparing it for a human reviewer. Your job is to make the reviewer's job easy and to be honest about what is and isn't verified. An unchecked box with a reason is worth more than a checked box you cannot back up.

**When to use this:** Any point in the dev loop where a PR is wanted — right after a code review, mid-story as a draft, or for a hotfix/chore with no story at all. This skill does not require a story to exist and does not require the story to be `done`.

**How this differs from the neighbouring workflows:**

- `bmad-code-review` — adversarial self-review of your own story *before* you open a PR. It may offer to hand off to this skill at the end; it does not build the PR itself.
- `bmad-review-pr-teammate` — the reviewer's seat on someone else's already-open PR.
- **This skill** — the author's seat: turn finished (or in-progress) work into a PR.

## Conventions

- Bare paths (e.g. `customize.toml`) resolve from the skill root.
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

- `project_name`, `user_name`, `communication_language`, `document_output_language`, `implementation_artifacts`
- `pr_template` = `{workflow.pr_template}` (resolves to `{project-root}/.github/pull_request_template.md` by default)
- `commit_template` = `{workflow.commit_template}` (resolves to `{project-root}/.github/commit_template.md` by default)
- `base_branch` = `{workflow.base_branch}`
- `title_format` = `{workflow.title_format}`
- `draft_default` = `{workflow.draft_default}`
- `verify_commands` = `{workflow.verify_commands}`
- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`

If the file at `{pr_template}` does not exist, HALT and tell the user this skill has nothing to fill in — either restore the template or point the workflow at a different one via `bmad-customize`.

**Read `{commit_template}` now and keep it as a persistent fact for the whole run.** It is the commit-message standard for this repo (Conventional Commits + reglas de estilo), and it governs every commit message this workflow drafts, as well as the PR title — per its own "Relación con el template de PR" section, the type of the main commit must match the PR's "Tipo de cambio", the scope must match the área in "Cambios principales", and the footer `Refs: <story_key>` must match the PR's "Story" field.

If `{commit_template}` does not exist, do **not** HALT — say so once, and fall back to plain Conventional Commits (`<tipo>(<scope>): <descripción>` in Spanish, imperative, lowercase, no trailing period).

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
- **NEVER** push, create a PR, or update a PR without an explicit, freshly-given confirmation in this run
- **NEVER** create a commit without an explicit, freshly-given confirmation in this run — a commit is only ever made at the commit gate of step 4, never earlier and never silently
- **NEVER** write a commit message that does not follow `{commit_template}`, and never bypass its hooks (`--no-verify` is forbidden)
- **NEVER** amend, rebase, squash or otherwise rewrite commits that already exist — this workflow only ever adds a new commit
- **NEVER** tick a checklist box without real evidence produced in this run
- **NEVER** invent acceptance-criteria evidence — say it is missing instead
- **ALWAYS** read entire step file before execution
- **ALWAYS** follow the exact instructions in the step file
- **ALWAYS** halt at checkpoints and wait for human input

## FIRST STEP

Read fully and follow: `./steps/step-01-resolve-context.md`
