---
pr_title: '' # set at runtime
pr_body: '' # set at runtime: the full Markdown body, in {pr_template}'s structure
preserved_notes: '' # set at runtime: human-written prose carried over when mode=update
---

# Step 3: Render the PR Body

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- This step is **read-only**. Nothing is published here — step 4 owns every gate.
- Write the body in `{document_output_language}` (Español), matching the template's own voice.
- **Never invent evidence.** An honest gap is information for the reviewer; a plausible sentence with nothing behind it is a lie in a document someone will merge on.

## INSTRUCTIONS

### 1. Load the template as the skeleton

Read `{pr_template}` in full. Keep its **exact section order and heading text**. Strip the HTML comments — they are instructions to the author, not content. Do not add sections it does not have, and do not drop sections you have nothing for (say what you have or say it is missing).

The current template's sections are: `## Resumen`, `## Story / Épica`, `## Cambios principales`, `## Criterios de aceptación cubiertos`, `## Resultado de code review`, `## Checklist`, `## Notas para el reviewer`. If the file on disk differs, the file wins.

### 2. Fill the narrative sections

**`## Resumen`** — 2 to 4 lines: what changed and why. Written for someone who has not read the story.

**`## Story / Épica`** — `- Story: ` + `` `{story_key}` `` in backticks, and `- Épica: ` + `{epic_ref}`. When there is no story, write `sin story — <hotfix|chore|spike>: <una línea de motivo>` and leave the épica line empty rather than guessing one.

**`## Cambios principales`** — bullets from `{changes_list}`, grouped by area (backend / frontend / migraciones / CI) when the diff spans several. Reference real paths. If the story's File List disagreed with the real diff, note that here.

**`## Criterios de aceptación cubiertos`** — one bullet per AC in `{ac_list}`, each with its evidence from `{ac_evidence}`: the test that covers it, the endpoint exercised, the file that implements it.

> **Hard rule:** when an AC has no evidence recorded in the story file and none was produced in this run, write `⚠️ sin evidencia registrada` for that AC. Never fill it with plausible prose. The reviewer needs to know which criteria are actually unverified.

When there is no story, replace the section body with `n/a — cambio sin story` and, if useful, one line on what a reviewer should convince themselves of instead.

### 3. Fill `## Resultado de code review`

The template asks for four bullets: `Decision-needed resueltos:`, `Patches aplicados:`, `Deferred:`, `Dismissed (noise):`.

- Fill all four from `{review_counts}` — counts, plus a one-line gist each when there are few enough to be useful. If any `[Review][Decision]` is still open, say so explicitly here (`2 resueltos, 1 abierto`), do not report only the resolved ones.
- For `Deferred:`, reconcile the story's `[Review][Defer]` items against `{deferred_relevant}` (the ledger). Report the count and, when they disagree, which items are in one and not the other.
- Surface any count discrepancy step 2 found between a prose `Completion Notes` claim and the actual bullets. One line is enough: `(la nota del story dice 3; la sección lista 2)`.

When `{review_ran}` is false, replace the four bullets with a single line: `No se ejecutó `bmad-code-review` para este cambio.` **Do not write four zeros** — a zero asserts that a review ran and found nothing, which is a different and false claim.

### 4. Render the checklist honestly

From `{checklist_state}`, preserving the template's exact box wording:

- `- [x] <texto de la casilla>` when the evidence rule was satisfied
- `- [ ] <texto de la casilla> — <razón>` otherwise

Never tick a box the state says is unchecked, even if you believe it is probably fine.

### 5. Fill `## Notas para el reviewer`

- Known risks and anything the reviewer should look at hardest.
- How to test manually, when it is not obvious.
- Any verification failure from step 2, with the relevant output tail.
- Anything you noticed while reading the diff that the story does not mention.
- When `{mode}` = `update`: `{preserved_notes}` goes here (see section 7).

### 6. Build the title

- With a story: apply `{title_format}` → `feat: {story_key} - {story_title}`. Use the story's real title, not a paraphrase.
- Without a story: derive the title from `{branch_commits}` (and, when the work is not committed yet, from the pending diff) following `{commit_template}` — its tipos table, Spanish, imperative, lowercase, no trailing period.
- Either way the title's **tipo** must match the checkbox you marked under "Tipo de cambio", because it becomes the commit message on squash-merge — and it is the same tipo the commit gate in step 4 will use if the commit still has to be made.
- When creating a draft for work in progress, do not encode "WIP" in the title — GitHub's draft flag already says that.

### 7. Update mode: do not clobber human prose

When `{mode}` = `update`:

1. Read the current body of `{existing_pr}` (from step 1, or `mcp__github__pull_request_read` with `method: "get"`).
2. Identify prose a human wrote that your regeneration would destroy — most often under `## Notas para el reviewer`, but also any section a reviewer or the author edited by hand. Carry it into `{preserved_notes}` and **append** your new notes below it under a dated sub-line. Never replace it.
3. Note which sections your update changes, so you can show the user a diff-shaped summary rather than a wall of text at the next step.

## NEXT

Read fully and follow `./step-04-confirm-publish.md`
