# Writing guide (content standard)

Audience: the reader described in config `profile` (background, field, why they read). If it is empty, ask first (SKILL.md §0). Write simplified Chinese; keep English terms at first mention（中文（English））; keep math, names, model and sensor names as-is. Plain words, short paragraphs, no hype, no filler.

## Section plan (adapt to the paper; keep keys short and stable)
| Group | Sections (key) | Must contain |
|---|---|---|
| 读前准备 | `overview` 一页速览 | `直` what the paper does in one picture; `原` the abstract's key sentences; Fig.1; `重` contributions as the authors list them; `数` headline numbers with refs; `讲` reading order (first pass / second pass / third pass) |
| | `prereq` 读前概念 | `术` only the concepts this paper needs (judged against the reader's background), each with a plain explanation; link the user's own notes/handbook if they have one |
| 问题与动机 | `problem`, `related` | why the problem is hard → which design choice each difficulty forces; how related work is positioned (table: prior work / gap the authors claim / this paper's answer); explicit assumptions and scope |
| 方法 | one section per component (`system`, `obs`, `action`, `reward`, `model`, `training`, …) | inputs → representation → network/algorithm → outputs → training; formulas with symbol-by-symbol explanation; hyperparameters with refs; a demo where it helps |
| 实验 | `setup`, `results`, `ablation`, … | task/success criterion, data sizes, trials, baselines and how they were built; full result tables re-typed; headline numbers recomputed; which split/metric each number uses; what failed |
| 结论与评价 | `conclusion`, `limits`, `relation`, `quiz` | authors' conclusion and future work (`原`/`讲`); limitations table (limitation / evidence ref / possible improvement) in `评`; links to the reader's field, background and current goal (`profile`) in `联`; 3–5 self-test questions with answers |

## Rules
- **Start every section with intuition** (`直` or the first lines of `讲`) before notation.
- **Every factual sentence has a ref.** Numbers: state baseline, data size, trials, condition. If the paper lacks something (control rate, seeds, number of trials), say so in `勘`; for comparison tables write "未报告".
- **Recompute** sums/percentages with python3; if they disagree with the paper, report in `勘`.
- **Opinions only in `评`.** Phrase as analysis ("这意味着…", "可以和导师/同学讨论…"), not as facts about the paper.
- **Explain every symbol** in a formula the first time; give units.
- **Tables over prose** for comparisons (prior work, hyperparameters, results, limitations).
- **Point out traps** in `坑`: which number the abstract reports, what is excluded from the input, train vs test split.
- **Original quotes**: 1–3 sentences each, the sentences the argument hinges on; not every paragraph.
- **Self-test**: questions that check understanding of the mechanism and the evidence (what is the input, why this design, what the ablation shows, how a headline number is computed), not trivia.
- **Card** (`paper.json`): fill every item in one line each, with refs; mark your own analysis "（助手分析）".
- Length guide: a 6–8 page conference paper ≈ 14–18 sections, 2–5 demos, 5–9 figures.

## Relation section
Use config `profile` and, if the user works in a project folder, its AGENTS.md / CLAUDE.md / notes: the reader's field, current task and background. Connect concretely (which component could be reused, which question to ask an advisor or colleague, what to try next). Do not guess personal facts about the reader or the authors; state anything unconfirmed as unconfirmed.
