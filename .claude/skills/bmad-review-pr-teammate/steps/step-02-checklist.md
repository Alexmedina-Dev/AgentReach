---
checklist_items: '' # set at runtime: parsed checkbox items from {checklist_template}
findings: '' # set at runtime: list of {section, item, verdict, comment_type, detail, location}
---

# Step 2: Walk the Checklist

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- Follow `{checklist_template}` as written. Do not substitute your own review methodology (no Blind Hunter / Edge Case Hunter / adversarial-general layer here — that is a different workflow, `bmad-code-review`, for a different seat).
- Read the actual source at each location before judging it — never rate a checklist item from the diff hunk alone. Open the file, check call sites, guards, and context that may live outside the changed lines.
- This step is read-only. Do not modify any files or GitHub state.

## INSTRUCTIONS

1. **Load `{checklist_template}` in full.** Parse every checkbox item (`* [ ] ...`) preserving its section heading, whatever the template's actual sections are called (e.g. "Puerta de entrada", "Diseño y arquitectura", "Reglas específicas del proyecto"). These become `{checklist_items}`.

2. **If a "Story/Épica" or spec context exists** (`{story_file}` set in step 1, or referenced in the PR body), read it now. Use it only to judge the checklist items that ask about AC coverage or story alignment — this workflow does not run its own separate spec audit on top of the checklist.

3. **Walk every section in the order it appears in `{checklist_template}`.** For each item:
   - Check it against `{diff_output}` and the real files it touches (per the RULES above).
   - Record a verdict: **cumple**, **no cumple**, or **no aplica** (with a one-line reason for "no aplica").
   - For anything that isn't a clean "cumple", write a concrete finding: what, where (`file:line`), and why it matters.

   **Special handling for the "Puerta de entrada" gate**: if any gate item fails (lint/type-check errors, unexplained suppressions), say so plainly up front — per the template, this is where a reviewer stops digging into everything else, though you may still note anything else you already noticed.

4. **Classify every finding using the template's own vocabulary** — nothing else:
   - `praise:` — something done well, say so
   - `nit:` — minor, author may ignore
   - `suggestion:` — an improvement, author's call
   - `issue:` — blocks merge, must be fixed
   - `question:` — you don't understand something, ask

   A real blocker is never softened into a `nit:` to be polite.

5. **Assign the template's own triage bucket** to each `issue:`/`suggestion:`/`question:` finding:
   - **Decision-needed** — the author must decide, not you
   - **Patch** — minor fix, author can apply without discussion
   - **Deferred** — valid, doesn't block this PR (note it should go in `deferred-work.md` if the project keeps one and the user wants it recorded there)
   - **Dismissed (noise)** — considered and doesn't apply, say why

6. Do not drop or hide anything found — even praise-worthy items get listed, since the template asks for them explicitly.

## NEXT

Read fully and follow `./step-03-present-post.md`
