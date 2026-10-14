---
name: paper-reading
description: "Turn one research paper (a PDF file, a PDF link / arXiv id, or a Zotero item) into a Chinese close-reading report (精读报告): a single self-contained HTML page with section-by-section explanation, key original paragraphs with page links back to the PDF, cropped original figures, re-typed tables, interactive demos of the method/data, critical analysis, self-test and a structured summary card; the reader highlights, comments and takes notes on it, saved as files by a local paper hub. Use when the user asks for 精读, 精读报告, 精读页, 做精读, or wants to deeply read one specific paper. Not for skimming several papers together (泛读/对照读)."
---

# Paper reading (精读报告)

Reply to the user in Chinese unless they ask otherwise. Works on macOS, Linux and Windows, in Claude Code, Codex or any agent that can run shell commands and look at images.

## 0. Before anything: is it installed, who is the reader?

Read `~/.config/paper-reading/config.json` (on Windows `%USERPROFILE%\.config\paper-reading\config.json`).

- **Missing** → the engine is not installed. Follow `INSTALL.md` in this skill folder (it tells the user what will happen and asks where to put things) before making any report.
- **Present** → it gives `root` (data root), `engine`, `data`, `python` (the engine's venv Python — use it for every `.py` engine script), `node`, `port`, `hub`, `reportsDir`, `profile`.
- **`profile` empty** → before the first report ask the user, in one short message: their background (e.g. "计算机硕士，刚入门机器人"), field / research direction, and why they read papers now (course, survey, thesis…). Save the answers into `profile` (keep the other keys). Write every report for that reader; never assume a field.

Below, `PY` = config `python`, `E` = config `engine`, `D` = `<config data>/<ID>`. Quote paths in commands (they may contain spaces or non-ASCII characters).

Start the hub (idempotent, safe to run every time): `PY E/hubctl.py start`. If it fails, see `references/hub.md`.

## The system you are producing for

```
<root>/                                    chosen by the user at install time
├── _paper-reading/
│   ├── engine/      server.py build.js template.html pdftool.py new_paper.py hubctl.py … .venv/ vendor/katex/
│   └── data/<ID>/   paper.json  source.pdf  src/NN_*.txt  figs/*.webp  demos/*.html  notes/ (user's — NEVER touch)
└── <reportsDir or the user's folder>/…/<report>.html     ONE file per paper, location = paper.json "out"
```

- Hub: `http://127.0.0.1:<port>/` lists all papers grouped by top-level folder; reports opened through it save notes as files in `D/notes/`.
- Build: `node E/build.js <ID>`. It embeds figures, demos and KaTeX into the report, checks every PDF page is covered by some section, and prints errors (KaTeX, missing files, out-of-range page refs). Fix until clean.
- Where the report goes: `<reportsDir>/<Author>_<Year>_<Short>.html` by default; if the user keeps a project folder with its own rules (AGENTS.md / CLAUDE.md), follow them and update the registers they ask for.

## Workflow

Read `references/workflow.md` (steps), `references/markup.md` (src format, paper.json) and `references/writing-guide.md` (content standard) before writing. Read `references/demos.md` before writing demos or cropping figures. `references/hub.md` covers install, storage and troubleshooting. `examples/Zhao2024-UnknownObjectRetrieval/` is a complete reference report (src, paper.json, demos; figures omitted).

## Getting the paper (Zotero is optional)

- **Local PDF** (most common): the user gives a path → `new_paper.py … --pdf <path>` copies it to `D/source.pdf`; page refs then open that PDF at the page in the browser.
- **Link / arXiv id / DOI**: tell the user the exact URL and ask before downloading; save it to your scratchpad, then use `--pdf`.
- **Zotero** (only if the user uses it and a Zotero tool/MCP is available): find the item, read metadata, get the PDF attachment path and keys; fill `zotero.item` / `zotero.pdf` so page refs open in Zotero. Adding `--pdf` as well is fine (browser links are used only when `zotero.pdf` is empty).
- Scanned PDF without a text layer (`pdftool.py info` says so): read from the page images only and say so in the report.

## Non-negotiables

1. **Read every page yourself**: `PY E/pdftool.py text <pdf> N` per page for text, and look at the rendered page images (`pdftool.py render`) for figures, tables and formulas. The build fails unless every page is claimed by a section (`@@ … | p.N`) or listed in `pagesSkipped` with a reason.
2. **Facts trace to the paper**: every number, claim and quote carries a page/figure/table ref (`[p.3]`, `[Table II]`); check each number against the source, recompute derived numbers (sums, percentages) with Python. Values read off a plot are labelled as estimates.
3. **Separate the paper from you**: your own analysis, criticism and ideas go only in `评` blocks (rendered as 助手分析); source problems (typos, inconsistencies, missing details) in `勘`. Never present your guess as the paper's statement; say "论文没有写" when it doesn't.
4. **Intuition before jargon**: pitch to the reader in `profile`; each section starts from a plain-language picture (`直`) before terms and formulas.
5. **Quote, don't transcribe**: `原` blocks hold short key passages (a few sentences), not whole sections; crop only the figures needed for understanding. Reports are for the user's own study.
6. **Never touch `notes/`**, never delete or rename a paper ID that has notes. Rebuilding keeps highlights (they re-anchor by quoted text within the same section key), so keep section keys stable when revising.
7. **Verify before reporting**: with a browser tool, open the report through the hub and check as in workflow.md §6. Without one, at least fetch the report from the hub (HTTP 200), make sure the build output is clean, and tell the user what you could not check visually.
8. Do not batch-produce reports in advance; make one when the user decides to read that paper closely. One report costs a lot of tokens and time (every page is read as text and image) — say so if the user asks for several.

## Report to the user

In Chinese, short: hub link and report path, number of sections / demos / figures, what to read first, notable source problems found, anything not done or uncertain. Then follow the user's project rules (if any) for registering the report.
