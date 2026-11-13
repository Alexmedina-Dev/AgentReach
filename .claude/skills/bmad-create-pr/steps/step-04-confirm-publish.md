---
committed: false # set at runtime
commit_messages: '' # set at runtime: the message(s) actually committed in this run
pushed: false # set at runtime
is_draft: false # set at runtime
pr_url: '' # set at runtime
published: false # set at runtime
---

# Step 4: Confirm and Publish

## RULES

- YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- **NEVER** run `git push` without an explicit, freshly-given confirmation in this run.
- **NEVER** call `mcp__github__create_pull_request` or `mcp__github__update_pull_request` without an explicit, freshly-given confirmation in this run.
- **NEVER** run `git add` or `git commit` without an explicit, freshly-given confirmation at the commit gate below — and never with a message that does not follow `{commit_template}`.
- **NEVER** use `--no-verify`, `--amend`, `git rebase`, `git reset` or `git stash`. If a hook rejects the message, fix the message; if the working tree needs surgery, that is the user's to resolve.
- A confirmation given earlier in the conversation, or in a previous run of this workflow, does not count. Ask again.
- The gates run in order — commit, then push, then publish. Each one only opens after the previous one is settled.

## INSTRUCTIONS

### 1. Show the PR

Present `{pr_title}` and the full `{pr_body}` as your message. Do not shorten, summarize or elide it — this is the artifact under review, and the user cannot approve what they cannot see.

When `{mode}` = `update`, lead with a short list of which sections change relative to the PR's current body, then show the full new body.

### 2. Commit gate

Only when `{has_uncommitted}` is true — i.e. the commit that this PR needs has not been made yet, either because the branch has no commits at all or because there is pending work on top of the ones it has.

#### 2.1 Draft the commit message

Re-read `{commit_template}` if it is not already in front of you, and draft the message **from the actual diff**, not from the story's wording:

- **Tipo** — one of the template's table (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `ci`, `revert`). It must match the type of `{pr_title}` and the checkbox marked under "Tipo de cambio" in `{pr_body}` — per the template, tipo del PR = tipo del commit principal.
- **Scope** — the module or área touched (`auth`, `checkout`, `orders`…), matching what `{pr_body}` lists under "Cambios principales". Omit it rather than inventing a catch-all like `misc` or `varios`.
- **Descripción** — Spanish, imperative ("agregar", not "agregado"), lowercase, no trailing period, ≤72 chars. It describes the change, not the process.
- **Cuerpo** — only when it earns its place: the *qué* and the *por qué*, wrapped at ~72 chars. The diff already shows the *cómo*.
- **Footer** — `Refs: {story_key}` whenever a story is set, so the commit traces back to the story without going through the PR. Add `BREAKING CHANGE: <explicación>` (and/or `!` after the type) when the diff actually breaks a contract.

**Atomicity check.** If the pending changes span more than one type — say a `feat` plus an unrelated `chore` of tooling — the template is explicit that this should be more than one commit. Say so and offer the split as an option below; do not silently bundle them under one type.

#### 2.2 Ask

**HALT** — show the exact message you would use, verbatim in a fenced block, together with the paths it would include (`{uncommitted_files}`), and ask:

**Hay cambios sin commitear. ¿Los commiteo con este mensaje?**
1. Sí, commitea todo así
2. Sí, pero ajusto el mensaje — <the user dictates it>
3. Divídelo en varios commits (te propongo el desglose)
4. Sigo sin commitear — esos cambios quedan fuera del PR
5. Me detengo para commitearlos yo

Present option 3 first when the atomicity check flagged mixed types.

- **Option 2** — take the user's wording, but still validate it against `{commit_template}` before using it. If it breaks the format (mayúscula inicial, tiempo pasado, punto final, tipo inválido), say so once, show the corrected version and ask them to confirm; their call wins if they insist.
- **Option 3** — propose the desglose as a numbered list of commits (each with its own full message and its own file set), **HALT** for approval, then apply them in order with a separate `git add <paths>` + `git commit` per entry. Never `git add -A` in this path.
- **Option 4** — continue with the changes left out. Everything downstream describes only what is committed, so re-check `{pr_body}`: if a section, a checklist box or an AC evidence line leans on work that stays uncommitted, correct it before publishing and tell the user what you changed.
- **Option 5** — stop the workflow here. Say plainly that nothing was committed, nothing was pushed and no PR was touched, and that re-running the skill afterwards picks everything up.

#### 2.3 Commit

On options 1–3 only:

1. Stage — `git add -A` for options 1 and 2, `git add <paths>` for each commit of option 3. Before staging, scan `{uncommitted_files}` for things that must not be committed (`.env`, credentials, `*.log`, large binaries, unrelated local scratch files). If any appear, **HALT** and ask before staging them; do not decide it yourself.
2. Commit — write the message to a temp file and run `git commit -F <tmpfile>` so the body and footer survive intact. Do not build multi-line messages out of stacked `-m` flags.
3. Record the message(s) in `{commit_messages}` and set `{committed}` = true.

**If a hook rejects the commit** (this repo runs `commit-message-check.yml`, and may run commitlint/husky locally), show the error verbatim, fix the *message* to satisfy it and retry once. If it still fails, stop and report it — bypassing the hook is not an option.

**If `git commit` fails for any other reason** (conflicted paths, nothing staged, missing identity), show the error verbatim and stop. Do not attempt a workaround.

#### 2.4 Refresh the git state

After a successful commit, re-run and update:

- `git status --porcelain` → `{has_uncommitted}` (should now be empty for options 1 and 2)
- `git log --oneline origin/{base_branch}..HEAD` → `{branch_commits}`
- `git log --oneline origin/{current_branch}..HEAD` → `{unpushed_commits}`

The new commit is unpushed by definition, so the push gate below now applies even if it did not a moment ago.

### 3. Push gate

Only when `{unpushed_commits}` is non-empty or `{remote_has_branch}` is false. **HALT** — show what would be pushed (commit count and oneline list) and ask:

**Falta publicar la rama. ¿Pusheo `{current_branch}` a origin?**
1. Sí, pushea
2. No, me detengo

On option 1 only: run `git push -u origin {current_branch}` and set `{pushed}` = true. If the push is rejected (non-fast-forward, protected branch, missing credentials), show the error verbatim and stop — do not attempt `--force` under any circumstances, and do not attempt a workaround.

On option 2: stop the workflow. Nothing is published.

### 4. Publish gate

**HALT** — ask, with the wording matching `{mode}`:

When `{mode}` = `create`:

**¿Creo el PR contra `{base_branch}`?**
1. Sí, créalo
2. Sí, pero como **draft**
3. No — esto se queda en el chat

When `{mode}` = `update`:

**¿Actualizo el PR #{existing_pr} con este contenido?**
1. Sí, actualízalo
2. No — esto se queda en el chat

Wait for the numbered choice. Set `{is_draft}` from the answer (option 2 in create mode; `{draft_default}` only decides which option you present first, never the outcome).

On the "no" option: stop here. The rendered body above is this workflow's entire output — say so, and mention the user can copy it manually or re-run the skill later.

### 5. Publish

**Create mode** — call `mcp__github__create_pull_request` with:

- `owner` = `{owner}`, `repo` = `{repo}`
- `base` = `{base_branch}`, `head` = `{current_branch}`
- `title` = `{pr_title}`, `body` = `{pr_body}`
- `draft` = `{is_draft}`

**Update mode** — call `mcp__github__update_pull_request` with `owner`, `repo`, `pullNumber` = `{existing_pr}`, `title` = `{pr_title}`, `body` = `{pr_body}`.

Set `{published}` = true and `{pr_url}` from the response.

If the call fails, show the error verbatim. The most likely causes are a PR already open for this branch (re-run the skill so step 1 resolves `update` mode) or the branch not being on the remote (section 3 was skipped or its push failed). Do not retry blindly.

### 6. Close

Report, briefly:

- The commit(s) created in this run, if `{committed}` is true — the subject line of each, and the fact that they follow `{commit_template}`. If the user chose to leave changes out (option 4), name the paths that stayed uncommitted.
- The PR URL, and whether it is a draft.
- Which checklist boxes went out **unchecked** and why — this is the part the user most needs to see, since it is what the reviewer will ask about.
- Any AC marked `⚠️ sin evidencia registrada`.
- Pending `{deferred_relevant}` entries, if any, as a reminder that they live in `deferred-work.md` and are not part of this PR.

Do not offer to merge the PR, request reviewers, or run anything else. This workflow ends here.
