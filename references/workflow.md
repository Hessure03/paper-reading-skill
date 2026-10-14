# Workflow: one close-reading report

From `~/.config/paper-reading/config.json`: PY = `python` (engine venv), E = `engine`, D = `<data>/<ID>`, ROOT = `root`. Scratch = your scratchpad / a temp dir (reading images never go into D). Commands below are the same on macOS, Linux and Windows; quote every path.

## 1. Locate the paper
- **PDF from the user** (path, or a link you downloaded after asking): note the path; metadata (title, authors, venue, year, DOI) comes from page 1 and the PDF's own text. Look up the DOI / venue only if the user allows web access.
- **Zotero** (if used and a Zotero tool is available): search the item (title/author/DOI) → metadata → children (PDF attachment key) → attachment path.
- Prefer the published version (venue + DOI). If only a preprint exists, say so in `venue` (e.g. `arXiv 2025（预印本）`).

## 2. Create the data folder
- ID = `<FirstAuthorSurname><Year>-<TwoOrThreeWords>` (ASCII only), e.g. `Zhao2024-UnknownObjectRetrieval`.
- `PY E/new_paper.py <ID> "<reportsDir>/<Author>_<Year>_<Short>.html" --pdf "<pdf path>"` (drop `--pdf` only when Zotero links are wanted and no local copy should be made); then fill `paper.json` (see markup.md). `pages` = page count from `PY E/pdftool.py info <pdf>`.

## 3. Read the whole paper
- `PY E/pdftool.py render <pdf> <scratch>/<ID> 110` → view every `p-NN.jpg` (several image reads in parallel if your tools allow).
- `PY E/pdftool.py text <pdf> N` per page for exact wording; add `--layout` for tables; `text <pdf> 1 7` dumps a range.
- While reading, note: problem & assumptions, inputs/outputs, every number with its ref, what each figure/table shows, things the paper does not state (rates, seeds, trial counts…), inconsistencies.
- Before writing, outline the sections (keys + page ranges) so every page is covered.

## 4. Figures
- `PY E/pdftool.py find <pdf> <page>` lists caption/table-caption boxes in pt; figures sit above captions, tables below.
- `PY E/pdftool.py crop <pdf> <page> <x> <y> <w> <h> D/figs/figN.webp [dpi]` (pt units, origin top-left; dpi 200 default, 250–300 for small text; `0 0 0 0` = whole page).
- View every crop; re-crop if anything is cut off. Typical size 10–90 KB.
- Re-type tables as markup tables rather than cropping them (searchable, highlightable); crop a table only if it is mostly graphics.

## 5. Write `src/NN_*.txt`
- One file per part (e.g. `01_intro`, `02_method`, `03_experiments`, `04_review`), written as you go so long jobs survive context compaction.
- Follow writing-guide.md for the section plan and block usage; demos per demos.md.
- Build after each file: `node E/build.js <ID>`; fix all errors.

## 6. Verify (through the hub)
- `PY E/hubctl.py start`, open the hub URL, click the card. Check: console has no errors; `.fig img` all load after scrolling; each demo responds; KaTeX renders (`.texerr` count 0); a page ref opens the PDF; phone width (375 px) has no page-level horizontal scroll.
- Highlight one phrase with a real mouse drag, add a comment, write a section note, toggle 读懂了; confirm `D/notes/data.json` and `D/notes/summary.md` update; reload and confirm the highlight re-applies.
- Remove the test data: if the paper had no notes before, delete `D/notes`; otherwise remove only your test entries through the UI.
- No browser tool (some Codex setups): fetch `<hub><out>` and check HTTP 200, make sure the build printed no 问题, and tell the user which visual checks are left for them.

## 7. Hand over
- Report to the user (SKILL.md). If the user keeps a project with registers (literature list, Zotero tag `精读`, comparison tables), update them as that project says; the `card` is meant for comparison tables.
- When the user later asks about their notes, read `D/notes/summary.md` (疑问清单 first) and answer; if a confusion comes from the report itself, improve the report (keep section keys), rebuild, and tell the user what changed.

## Updating a report later
- Edit src / paper.json / demos, rebuild. Never rename section keys that have notes; adding sections is fine. If a key must change, tell the user that highlights in that section will show as "未能定位" (they stay in the summary).
- Moving the report: change `out`, rebuild, delete the old html. Notes are keyed by ID, not path.
- Published version replaces a preprint: update metadata, replace `source.pdf`, update page refs (page numbers usually change), rebuild, check refs.
