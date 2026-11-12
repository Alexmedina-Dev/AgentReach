---
owner: '' # set at runtime
repo: '' # set at runtime
pr_number: '' # set at runtime
pr_title: '' # set at runtime
pr_body: '' # set at runtime
base_branch: '' # set at runtime
head_branch: '' # set at runtime
pr_author: '' # set at runtime
diff_output: '' # set at runtime
story_key: '' # set at runtime (or empty if none found)
story_file: '' # set at runtime (path or empty)
---

# Step 1: Resolve the PR

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- The prompt that triggered this workflow IS the intent — not a hint.
- Do not modify any files or GitHub state. This step is read-only.

## INSTRUCTIONS

1. **Find the PR reference.**

   **Tier 1 — Explicit argument.** Did the user give a PR number, URL, or paste one this message? Extract `{pr_number}` (and `{owner}`/`{repo}` if the URL carries them).

   **Tier 2 — Recent conversation.** Do the last few messages name a PR number or URL?

   **Tier 3 — Ask.** HALT. Ask the user: **¿Qué PR quieres que revise? (número o URL)**

2. **Resolve `{owner}`/`{repo}`** if not already known from a full URL: run `git remote get-url origin` and parse the `owner/repo` from it. If ambiguous or it fails, ask the user.

3. **Fetch PR metadata.** Call `mcp__github__pull_request_read` with `method: "get"` for `{owner}`/`{repo}`/`{pr_number}`. Set `{pr_title}`, `{pr_body}`, `{base_branch}` (from `baseRefName`), `{head_branch}` (from `headRefName`), `{pr_author}`.

   If the PR does not exist or is inaccessible, HALT and tell the user.

   If the PR is already `MERGED` or `CLOSED`, tell the user and ask whether to continue anyway (a historical/retroactive review) or stop. HALT for their choice.

4. **Fetch the diff.** Call `mcp__github__pull_request_read` with `method: "get_diff"`. Set `{diff_output}`.

   If `{diff_output}` is empty, HALT and tell the user there is nothing to review.

5. **Find a linked story, if any.** Scan `{pr_title}` and `{pr_body}` for a story key pattern (e.g. `1-2-user-auth`, "Story 1.5", "Story: `1-6-...`"). If found and a matching file exists under `{implementation_artifacts}` (or the path the PR body names), set `{story_key}` and `{story_file}`. If none found, leave both empty — this is not required for the review to proceed.

6. Sanity check: if `{diff_output}` exceeds approximately 3000 lines, warn the user and offer to chunk the review by file group.
   - If the user opts to chunk: agree on the first group, narrow `{diff_output}` accordingly, and list the remaining groups for the user to note for follow-up runs.
   - If the user declines: proceed as-is with the full diff.

### CHECKPOINT

Present a summary before proceeding: PR title, author, base←head branches, diff stats (files changed, lines added/removed), and the linked story if found. HALT and wait for user confirmation to proceed.

## NEXT

Read fully and follow `./step-02-checklist.md`
