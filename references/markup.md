# Source format

## paper.json (`data/<ID>/paper.json`)
```json
{
  "id": "Zhao2024-UnknownObjectRetrieval",            // = folder name; storage key for notes, never change
  "out": "reports/Zhao_2024_UnknownObjectRetrieval.html",  // relative to the data root; first folder = hub group
  "short": "Zhao 2024 · 窄缝取物",                     // top bar + tab title
  "title": "…English title…", "titleZh": "…中文译名…",
  "authors": ["…"], "venue": "ICRA 2024", "year": 2024,
  "doi": "10.1109/…", "url": "",                      // url: project page if any
  "zotero": {"item": "", "pdf": ""},                   // optional: Zotero item key, PDF attachment key → zotero:// links
  "pdf": "source.pdf",                                 // local copy in data/<ID>/ → page links open it (used when zotero.pdf is empty)
  "pages": 7,                                          // PDF page count (coverage check)
  "pagesSkipped": {"7": "参考文献"},                    // pages no section covers, with reason
  "tags": ["…"],                                       // shown on the report and hub card, used by hub filter
  "macros": {"\\E": "\\mathbb{E}"},                    // optional KaTeX macros
  "card": { "一句话": "", "问题与动机": "", "方法": "", "实验与数据": "", "结果": "", "局限": "", "与我的关系": "" }
}
```
`sections` and `built` are written by the build. `card` becomes the last section (结构化卡片) and is what comparison tables are filled from; values are one line each, may contain `$math$`, `**bold**` and refs. The keys are free: add field-specific ones the user cares about (e.g. 硬件 / 数据集 / 样本量 / 理论假设) and keep the same keys across the user's papers so cards line up in a comparison table.

## src/NN_*.txt
Read in file-name order. UTF-8.
```
## 方法                                       ← TOC group heading
@@ obs | 观测：机器人每一步"摸到"什么 | p.3      ← section: key | title | source pages
直: plain-language picture first…
原: [p.3] Short English quote from the paper.
讲: …
```
- Section line `@@ key | title | pages`: key = lowercase letters/digits/`-`, unique and **stable** (notes attach to it); pages like `p.3`, `p.2-3`, `p.1, p.4-5`; pages can be omitted for sections that cover no page.
- A line `X: …` with a known tag starts a block; following lines continue it until the next tag, `@@` or `##`. A blank line inside a block starts a new paragraph.
- Inside blocks: lines starting `| ` form a table (cells separated by ` | `, first row = header); lines starting `- ` form a list.

| Tag | Shown as | Use for |
|---|---|---|
| `直` | 直观 | everyday-language picture of the idea, before any jargon |
| `原` | 原文 p.N | short key passage in English; MUST start with `[p.N]` (label links to that PDF page) |
| `讲` | 讲解 | explanation, step by step; what each symbol means; why the design |
| `术` | 术语 | term cards: **Chinese（English）**：plain explanation |
| `式` | 公式 | whole block is one display formula (no `$$`) |
| `重` | 重点 | must-remember results, contributions, assumptions |
| `数` | 关键数字 | numbers with refs, baselines and conditions; tables of results |
| `坑` | 易错 | easy misreadings (which metric, which split, what is not in the input) |
| `评` | 助手分析 | your critique, ideas, open questions — the only place for opinions |
| `勘` | 校核 | source typos, inconsistencies, missing details ("论文没有给出…") |
| `联` | 联系 | links to other papers, the reader's background and goals (config `profile`), earlier sections |
| `题` `提` `答` `解` | 题目 / 提示 / 答案 / 解答 | self-test; 提/答/解 hidden until clicked |
| `图` | figure | `图: figs/fig2.webp | caption with [Fig.2] and [p.3]` (one per line) |
| `演` | demo | `演: demos/obs.html` (fragment inlined; see demos.md) |

## Inline
- Math `$…$`, display `$$…$$` (KaTeX, pre-rendered at build).
- `**bold**`, `` `code` ``, links `[text](url)` (relative links resolve from the report's location).
- Refs: `[p.3]`, `[p.3–4]`, `[Fig.4]`, `[Table II]`, `[Eq.(3)]`, `[Sec. IV-B]`, combined `[Fig.4, p.5]`. Anything containing `p.N` links to that page of the PDF (Zotero if `zotero.pdf` is set, else the local `pdf`).
- Plain citation numbers like `[14]` stay as text.

## Build errors you will see
- `无标签的行` — a line after `图:`/`演:` or outside a block; give it a tag (e.g. put a table under `数:`).
- `以下页没有被任何小节覆盖` — add `| p.N` to a section that discusses that page, or add it to `pagesSkipped` with a reason.
- KaTeX errors print the formula; common fixes: `\mathrm{}` for upright subscripts, escape `\{ \}`, no `\boxed{aligned}`.
