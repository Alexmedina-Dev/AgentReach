---
final_verdict: '' # set at runtime: "APPROVE" | "REQUEST_CHANGES" | "COMMENT"
review_body: '' # set at runtime: full Markdown review body
posted: false # set at runtime
---

# Step 3: Present, Decide Verdict, Optionally Post

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- **NEVER** call `mcp__github__pull_request_review_write` without an explicit, freshly-given confirmation from the user in this run.

## INSTRUCTIONS

### 1. Assemble the review body

Render `{review_body}` as Markdown, in `{checklist_template}`'s own structure and vocabulary:

- Short opening: what you reviewed (PR title/number, story if linked) and confirmation you read the story/diff, not just the title.
- One subsection per checklist section that had anything worth flagging (skip sections that were clean — say "checklist técnico general: sin hallazgos" or equivalent rather than padding).
- Each finding as a bullet: `praise:` / `nit:` / `suggestion:` / `issue:` / `question:` prefix, the detail, `file:line`, and its triage bucket (Decision-needed / Patch / Deferred / Dismissed (noise)) where applicable.
- A closing line naming any gate failures from the "Puerta de entrada" section explicitly, if there were any.

### 2. Present it to the user in chat

Show the full `{review_body}` as your message. Do not shorten or summarize it away — this is the actual review content.

### 3. Determine and confirm the final verdict

Propose a verdict based on the findings, using the template's own rule ("si de verdad bloquea, es `issue:`"):
- Any unresolved `issue:` → propose **Request changes**
- Only `question:`/`suggestion:`/`nit:`/`praise:`, no blocking `issue:` → propose **Comment** or **Approve** (Approve if genuinely nothing outstanding, Comment if you have open questions you want answered first)

HALT — ask the user:

**Con base en estos hallazgos propongo: `<propuesta>`. ¿Confirmas el veredicto final?**
1. Sí, `<propuesta>`
2. No, quiero otro veredicto (dime cuál)
3. No publiques nada, esto se queda solo en el chat

Wait for the numbered choice. Set `{final_verdict}` from their answer (map "Approve" → `APPROVE`, "Request changes" → `REQUEST_CHANGES`, "Comment" → `COMMENT`).

If the user picks option 3: stop here. Do not proceed to step 4. This workflow's output is the chat message above, nothing more.

### 4. Confirm publishing

HALT — ask the user explicitly, even though they already confirmed a verdict:

**¿Publico esta review en el PR #{pr_number} de GitHub ahora, como `{final_verdict}`?**
1. Sí, publícala
2. No, solo la quería aquí en el chat

Wait for the numbered choice.

- If "No": stop here. Nothing is posted.
- If "Sí": proceed to step 5.

### 5. Publish

Call `mcp__github__pull_request_review_write` with `method: "create"`, `owner`/`repo`/`pullNumber` = `{pr_number}`, `event` = `{final_verdict}`, and `body` = `{review_body}`.

Set `{posted}` = true. Present the user the PR URL and confirm the review is live.

### 6. Close

Summarize: verdict given, whether it was posted, and counts of `issue:`/`suggestion:`/`question:`/`nit:`/`praise:` findings.
