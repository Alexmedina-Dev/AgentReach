---
ac_list: '' # set at runtime: numbered acceptance criteria from the story
ac_evidence: '' # set at runtime: per-AC evidence, or an explicit "missing" marker
changes_list: '' # set at runtime: the main changes, derived from the story + diff
review_ran: false # set at runtime: whether a code review is recorded in the story
review_counts: '' # set at runtime: {decision, patch, dismissed} counts + open/resolved split
deferred_relevant: '' # set at runtime: deferred-work entries tied to this story
sprint_synced: false # set at runtime
verify_results: '' # set at runtime: per-command {id, ran, passed, output_tail}
checklist_state: '' # set at runtime: per-box {checked, reason}
---

# Step 2: Gather Evidence

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- Everything in this step except the verification commands is **read-only**.
- The verification commands are the only thing you may execute, and only the ones the user approves in this run. They are non-mutating by construction — if one of them would write to the repo or the database, do not run it and say why.
- **Evidence means evidence.** A box gets ticked because something was checked in this run, not because it is plausible.

## INSTRUCTIONS

### 1. Read the story content

Skip this section entirely when there is no `{story_file}`.

- `## Acceptance Criteria` — the numbered list → `{ac_list}`. Keep any `> Nota de alcance:` blockquote as context; it often bounds what the AC actually claims.
- `## Tasks / Subtasks` — the `- [x]` / `- [ ]` tree, to know what was actually completed.
- `## Dev Agent Record` → `### Completion Notes List` and `### File List` (split into `**Nuevos:**` / `**Modificados:**`) → the raw material for `{changes_list}`.

Build `{changes_list}` by reconciling the story's File List against `{changed_files}` from step 1. When they disagree, trust `{changed_files}` — it is the real diff — and note the discrepancy for the reviewer notes.

### 2. Count the code-review findings

The code review does **not** write a separate report; it appends its findings into the story file. Its heading level and position vary between stories, so:

- Match `Review Findings` at **any** heading level — the regex is `^#{2,4}\s*Review Findings`, not an anchored `###`. It has been seen as `###` nested inside `## Tasks / Subtasks`, as `###` under `## Dev Agent Record`, and as a top-level `##`.
- Also pick up the sibling variants some stories use: `### Patch (aplicados)`, `### Diferidos`, `### Descartados como ruido (no accionables)`, `### Decisión requerida (resuelta)`, `### Code Review — Patches aplicados (<fecha>)`.

Within those sections, count the tagged bullets → `{review_counts}`. The four tags in use are:

- `[Review][Decision]` → decision-needed
- `[Review][Patch]` → patches applied
- `[Review][Defer]` → deferred
- `[Review][Dismiss]` → dismissed as noise

For each one, record whether its checkbox is `- [x]` (resolved) or `- [ ]` (still open). The open/resolved split matters for the checklist.

**Tags are not the whole story — do not stop at a tag count.** Some stories record a bucket as an untagged prose subsection instead. Story `1-9-formato-numerico-es-co-consistente` is the worst case: three `[Review][Defer]` tags, but its dismissed items live as plain bullets under `### Descartados como ruido (no accionables)` with no tag at all, so a tag-only count reports zero dismissals where there were several. So, per bucket:

1. Count the tagged bullets.
2. **Plus** count the untagged bullets under the matching prose subsection, when one exists.
3. Cross-check against `### Completion Notes List`, which usually states the counts in prose (e.g. *"0 decision-needed, 0 patch, 3 deferidos, 3 descartados como ruido"*).

When the prose note and your count disagree, **say so in the PR body** rather than silently picking one — in `1-9` the note claims 3 dismissals and the section lists 2. That discrepancy is exactly the kind of thing a reviewer should know about.

If no `Review Findings` section exists at all, set `{review_ran}` = false and leave `{review_counts}` empty. Do not represent this as four zeros — "no review ran" and "a review ran and found nothing" are different claims.

### 3. Read the deferred-work ledger

Read `{implementation_artifacts}/deferred-work.md`. It uses the legacy freeform format: `## Deferred from: code review of <story_key> (<fecha>)` or `## Deferred from: dev of <story_key> (<fecha>)` headings with flat bullets and no `DW-` IDs.

Collect every bullet under a heading naming `{story_key}` → `{deferred_relevant}`. When there is no story, leave it empty and treat the corresponding checklist box as `n/a`.

Reconcile this against the `[Review][Defer]` items you counted in the story file: the story records what the review decided to defer, the ledger records what actually got written down. When a `[Review][Defer]` item has no counterpart in the ledger, that item was deferred and then lost — flag it for the reviewer notes rather than reporting a clean state.

### 4. Check the sprint-status sync

Compare `development_status[{story_key}]` in `sprint-status.yaml` against the `Status:` line in the story file. Equal → `{sprint_synced}` = true. Different → false, and record the exact mismatch (`archivo: done` vs `sprint-status: review`).

### 5. Offer the verification commands

Cross `{changed_files}` against the `paths` globs of each `{verify_commands}` entry to determine which apply. If none apply (e.g. the diff only touches docs or config), say so and skip to section 6 with both verification boxes marked `n/a` and the reason.

**HALT** — show the applicable commands verbatim (label, `cwd`, and the exact command line) and ask:

**Estos son los comandos de `ci.yml` que aplican a este diff. ¿Los corro para tener evidencia real del checklist?**
1. Sí, corre todos
2. Quiero elegir cuáles
3. No, no corras nada — las casillas quedarán sin marcar

Wait for the numbered choice. Run **only** what was approved. For each command record `{verify_results}`: whether it ran, whether it passed, and — on failure — the tail of the output (the failing assertions or lint errors, not the whole log).

**If a command fails, do not continue silently.** HALT and ask:

**`<comando>` falló. ¿Qué hago?**
1. Me detengo aquí para que lo arregles
2. Sigo — la casilla queda sin marcar y anoto el fallo en las notas para el reviewer

Option 1 ends the workflow: nothing was pushed and no PR was touched, so stopping costs nothing.

### 6. Compute the checklist state

Fill `{checklist_state}` for the five boxes of `{pr_template}`. A box is `[x]` **only** when its evidence rule below is satisfied; otherwise it is `[ ]` with the concrete reason attached.

| Box | `[x]` only when | Otherwise `[ ]` with reason |
|---|---|---|
| Tests pasan localmente | a `*-tests` command ran **in this run** and passed | `no ejecutado en esta corrida` / `falló: <resumen>` / `sin job de tests de frontend en ci.yml` when the diff is frontend-only |
| Lint / type-check sin errores | a `*-lint` command ran in this run and passed | same shape as above |
| Code review (`bmad-code-review`) ejecutado y findings resueltos | `{review_ran}` is true **and** no `[Review][Decision]` remains unchecked | `no se ejecutó bmad-code-review para este cambio` / `quedan N decision-needed abiertos` |
| Sprint status (`sprint-status.yaml`) sincronizado | `{sprint_synced}` is true | the exact mismatch |
| Sin deferred-work pendiente relevante a este cambio | `{deferred_relevant}` is empty | `N entradas pendientes` + the list |

When there is no story, the last three boxes are `[ ]` with `n/a — cambio sin story`.

Do not present this table to the user yet — step 3 renders it inside the PR body, which is where they will review it.

## NEXT

Read fully and follow `./step-03-render-body.md`
