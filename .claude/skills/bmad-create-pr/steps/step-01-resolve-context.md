---
owner: '' # set at runtime
repo: '' # set at runtime
current_branch: '' # set at runtime
mode: '' # set at runtime: "create" | "update"
existing_pr: '' # set at runtime: PR number + title + body when mode=update, else empty
story_key: '' # set at runtime (or empty when running without a story)
story_file: '' # set at runtime (path or empty)
story_title: '' # set at runtime (or empty)
story_status: '' # set at runtime: backlog|ready-for-dev|in-progress|review|done, or empty
epic_ref: '' # set at runtime (e.g. "epic-1") or empty
has_uncommitted: false # set at runtime
uncommitted_files: '' # set at runtime: porcelain list of modified/untracked paths
unpushed_commits: '' # set at runtime: list of oneline commits not on the remote base
remote_has_branch: false # set at runtime
changed_files: '' # set at runtime: paths changed vs the base branch (committed + uncommitted)
diff_stat: '' # set at runtime: git diff --stat summary
branch_commits: '' # set at runtime: oneline commits of this branch vs base
---

# Step 1: Resolve Context

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- The prompt that triggered this workflow IS the intent — not a hint.
- This step is **read-only**. Do not modify any files, do not touch git state, do not touch GitHub state. No `git add`, no `git commit`, no `git push`, no fetch that rewrites refs is needed beyond `git fetch origin {base_branch}` — and even that only if the local ref is missing.

## INSTRUCTIONS

### 1. Read the git state

Run these and record the results:

- `git rev-parse --abbrev-ref HEAD` → `{current_branch}`
- `git remote get-url origin` → parse `{owner}`/`{repo}` from it
- `git status --porcelain` → `{has_uncommitted}` (true when non-empty) and `{uncommitted_files}` (the full list — you will show it at the commit gate in step 4, and you need it to draft the commit message)
- `git ls-remote --heads origin {current_branch}` → `{remote_has_branch}` (true when non-empty)
- `git log --oneline origin/{base_branch}..HEAD` → `{branch_commits}`
- `git log --oneline origin/{current_branch}..HEAD` → `{unpushed_commits}` (empty string when `{remote_has_branch}` is false — in that case *every* commit is unpushed, note it as "rama nueva, sin publicar")

If `origin/{base_branch}` does not resolve, run `git fetch origin {base_branch}` once and retry. If it still fails, HALT and tell the user the base branch `{base_branch}` is not reachable from this clone.

### 2. Refuse to open a PR from an integration branch

If `{current_branch}` equals `{base_branch}` or `main`: **HALT**. Tell the user plainly that a PR cannot be opened from the integration branch, and that they need a feature branch first. Do not offer to create the branch for them — that is their call and outside this workflow.

### 3. Resolve the story

Try in order and stop at the first that resolves:

**Tier 1 — Explicit argument.** Did the invocation carry a `story_key`, a story file path, or an explicit "sin story" / `--no-story`? Use it. (`bmad-code-review` hands off with the `story_key` this way.)

**Tier 2 — Branch name.** Does `{current_branch}` encode a story? The convention here is `feature/<username>-story-<epic>.<story>` (e.g. `feature/nvega-azt-story-1.10`). **Convert the dot to a dash** (`1.10` → `1-10`) and glob `{implementation_artifacts}/1-10-*.md`. A single match resolves `{story_key}` (the filename stem) and `{story_file}`.

**Tier 3 — Sprint status.** Read `{implementation_artifacts}/sprint-status.yaml`. Look for stories in `development_status` whose value is `review` or `done` **and** whose `assigned_to` entry matches `{user_name}` or `git config user.name`. If exactly one matches, propose it; if several, list them and ask which.

**Tier 4 — Ask.** HALT. Ask the user:

**¿A qué story corresponde este PR?**
1. `<candidatos que encontraste, si hay>`
2. Sin story — es un hotfix / chore / spike

Wait for their answer. "Sin story" is a fully supported path: leave `{story_key}`, `{story_file}`, `{story_title}`, `{story_status}` and `{epic_ref}` empty and continue.

### 4. Read the story file

Only when `{story_file}` is set:

- `{story_title}` — from the `# Story <epic>.<story>: <título>` H1.
- `{story_status}` — from the bare `Status: <estado>` line that follows the H1 (it is **not** in the frontmatter).
- `{epic_ref}` — the `epic-<n>` key that owns this story in `sprint-status.yaml`.

**Do not gate on the status.** A story in `in-progress` or `review` is a legitimate reason to open a draft PR mid-loop. Just surface the status at the checkpoint so the user sees it.

### 5. Check whether a PR is already open for this branch

Call `mcp__github__list_pull_requests` for `{owner}`/`{repo}` with `head: "{owner}:{current_branch}"` and `state: "open"`.

- One result → `{mode}` = `update`, and record its number, title and body in `{existing_pr}` (fetch the body with `mcp__github__pull_request_read` `method: "get"` if the list response does not carry it).
- No results → `{mode}` = `create`.
- More than one → list them and HALT asking which one to update.

Never treat an already-open PR as an error and never try to create a second one for the same branch.

### 6. Compute the diff against the base

- `git diff --stat origin/{base_branch}...HEAD` → `{diff_stat}`
- `git diff --name-only origin/{base_branch}...HEAD` → committed paths

When `{has_uncommitted}` is true, these commands only see what is already committed, and on a branch whose work has not been committed yet they see nothing at all. So also record what is pending and **merge both sets into `{changed_files}`**, keeping the two apart in your head — committed vs. pendiente de commit:

- `git diff --stat HEAD` → uncommitted tracked changes (append its summary to `{diff_stat}` under a "sin commitear" heading)
- `git status --porcelain` (already read in section 1) → untracked files too

`{changed_files}` is what decides which `verify_commands` entries apply in step 2 and what step 3 describes, so it must cover the work that will actually end up in the PR — including the changes that are still to be committed at step 4's commit gate.

If both sets are empty: HALT — there is nothing to open a PR for.

If the committed set is empty and only the uncommitted set has content, this branch has **no commit yet**. That is a supported path, not an error: carry on, and say at the checkpoint that the commit will be offered at the end of the workflow.

### CHECKPOINT

Present a summary and **HALT** for confirmation before proceeding:

- `{current_branch}` → `{base_branch}`
- Action: *crear PR nuevo* or *actualizar el PR #N — `<título actual>`*
- Story: `{story_key}` — `{story_title}` (estado: `{story_status}`), or *sin story*
- `{diff_stat}`
- **Higiene de git**, stated plainly when it applies:
  - cambios sin commitear (list them) — se te ofrecerá commitearlos con el formato de `{commit_template}` antes de publicar
  - la rama no tiene ningún commit propio todavía — el commit del PR está pendiente
  - commits sin pushear (count) — hay que pushear antes de abrir el PR
  - la rama no existe en el remoto todavía
- If `{story_status}` is set and is not `done`, say so explicitly and note that a draft PR is probably what they want.

## NEXT

Read fully and follow `./step-02-gather-evidence.md`
