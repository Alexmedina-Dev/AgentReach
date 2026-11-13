# Design brief: 3 visual proposals for an AI-access report (copy and paste everything below)

## 1. What AgentReach is
AgentReach is an open-source, read-only tool. It shows what an AI agent could reach in a developer's environment (files, settings, credentials, programs). Every result comes with evidence and a confidence level. It never changes anything and never shows secret values.

## 2. Who reads the report
Developers, including people who are new to security. Use plain language. No acronyms or codes without a short explanation. Write like you talk to a smart colleague.

## 3. What the report must show
1. A **summary by level** at the top (how many findings per level, plus "could not check").
2. **One card (or row) per finding.** Every finding has exactly **8 fixed fields, always in this order**:
   1. Location and line
   2. What it is, and whose it is
   3. Level, and why
   4. Unrelated to the task (yes / no / not determined)
   5. Platform and agent
   6. Agent rules (what the agent's own rules say)
   7. What to do
   8. What it means
3. A **fixed section "What AgentReach could not check"**. It always appears, even when empty. Two parts: "In this folder" and "Tool limits".
4. A visible notice: **"No secret values are shown."**
5. **Filters and search** (by level, by text).
6. Language buttons **EN** and **ES**. All text in both languages (the data has both).

## 4. Levels and color meaning
| Level | Color | Icon and shape (must be different) |
|---|---|---|
| Verified | red `#FF6B6B` (dark theme) | solid octagon with "!", thick border |
| Potential | amber `#FFB224` | triangle with "!" |
| Hypothesis | gray `#A9BDB9` | diamond with "?", dotted border |
| Could not check | violet `#B9A2FF` | circle with a slash, dashed border |
| OK / actions ("What to do") | mint `#3DF5D0` | check mark / arrow |
| Information (notices) | blue `#6DB6FF` | circle with "i" |

Rules:
- Color is never the only signal. Each level also has its own icon, shape and word.
- Red is used for "Verified" only. Nothing else may be red.
- Text contrast must be at least **4.5:1** (icons and borders at least 3:1), in both themes.

## 5. Brand palette (exact)
- Background `#0B1114`
- Surface `#121C20`
- Mint `#3DF5D0` (brand accent, "OK", actions)
- Amber `#FFB224`
- Text `#EAF4F2`
- Secondary text `#A9BDB9`
- Muted text `#7C928E`

**Palette A is the default.** (Red only for "Verified", as above.) For the light theme, keep it bold and colorful, not dull white: pale mint page `#DFF5EF`, white cards, dark mint `#005F4D` for text, deep amber `#7A4300` for amber text, dark red `#B3201A`, violet `#5A3DC0`, blue `#0A58A8`, gray `#3A524D`.

## 6. Technical rules (strict)
- **One single HTML5 file**, static HTML + CSS3. Minimal JavaScript only (filters, search, language, theme).
- **Load nothing external.** No web fonts, no scripts, no images, no CDN, no `<link>` to other sites. Use system fonts. Draw icons with inline SVG or CSS. No network calls (no fetch, no forms that send data).
- **Do not store data.** No localStorage, cookies or similar.
- The sample data goes **inside the HTML** (copy it from the JSON I attach).
- Buttons **EN** and **ES**.
- **Dark theme by default**, plus a bold light theme with a toggle. Respect `prefers-color-scheme` and `prefers-reduced-motion`.
- Responsive (works at phone width, no horizontal page scroll) and fully usable with the keyboard (visible focus, correct buttons, labels, landmarks).

## 7. What I expect from you
Give me **3 DIFFERENT visual proposals**. For example:
1. Cards (one card per finding).
2. Dense table with a side panel for details.
3. Timeline, or grouped by file.

(You may pick other ideas, but they must look and work clearly different.)

For each proposal give me:
- A complete, self-contained HTML file in its own code block.
- **One sentence** that explains the idea.

Important:
- **Do NOT invent features.** Only what is listed in section 3.
- Use **ONLY the sample data** I attach. Do not add findings, fields, names, paths or numbers.
- Do not add tracking, analytics, or anything that talks to a server.

## 8. How I will judge your proposals
1. All 8 fields appear, in the correct order, for every finding.
2. The fixed section "What AgentReach could not check" and the notice "No secret values are shown" are visible.
3. Levels can be told apart without color (icon, shape and word).
4. Contrast is at least 4.5:1 for text in both themes.
5. Brand colors are exact. Red appears only for "Verified".
6. Zero external requests. The file works offline.
7. EN and ES both work, and all text changes.
8. Filters and search work. Keyboard works. Phone width works.
9. Plain language, no unexplained codes.
10. The 3 proposals are truly different, and the idea is easy to understand in a few seconds.
