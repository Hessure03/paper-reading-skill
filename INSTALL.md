# INSTALL.md — instructions for the AI agent installing this skill

You (Claude Code, Codex or another coding agent) were asked to install the **paper-reading** skill from
`https://github.com/Hessure03/paper-reading-skill`. Follow these steps in order. Talk to the user in their language
(Chinese if they write Chinese). **Do not change anything on the machine before step 2 is answered.**

## Step 1 — Look first (read-only)

1. Detect the OS (macOS / Linux / Windows) and which agent you are.
2. Find Python ≥ 3.9 (`python3 --version`; on Windows try `py -3 --version`, then `python --version`) and Node.js ≥ 18 (`node --version`).
3. Check if it is already installed: does `~/.config/paper-reading/config.json` exist (Windows: `%USERPROFILE%\.config\paper-reading\config.json`)? Does a skill folder already exist at the locations in the table below?
4. Check whether port 8614 on 127.0.0.1 is free (e.g. try to fetch `http://127.0.0.1:8614/_ping.gif`; any answer means it is taken).

## Step 2 — Tell the user, then ask (wait for answers)

Send one message that covers **all** of the following, briefly and concretely (fill in the real paths for this machine):

**What it does**: makes a Chinese close-reading report (精读报告) for one paper from a PDF (Zotero optional): section-by-section explanation, short original quotes with page links, cropped figures, re-typed tables, small interactive demos, critique, self-test and a summary card. The reader highlights and takes notes in the browser; notes are saved as files by a small local web service.

**What will be installed where**:
| Item | Location |
|---|---|
| Skill files (instructions, engine source, ~250 KB) | Claude Code: `~/.claude/skills/paper-reading/` · Codex: `~/.agents/skills/paper-reading/` (Windows: under `%USERPROFILE%`) |
| Engine + Python venv (PyMuPDF, Pillow, ~60–100 MB) + KaTeX (~1.5 MB from registry.npmjs.org, sha512-checked) | `<data root>/_paper-reading/engine/` |
| Paper data, original PDFs, your notes | `<data root>/_paper-reading/data/` |
| Reports (one .html per paper) | `<data root>/reports/` by default |
| Settings (root, port, reader profile) | `~/.config/paper-reading/config.json` |
| Optional login item | macOS `~/Library/LaunchAgents/io.github.paper-reading.hub.plist` · Linux `~/.config/systemd/user/paper-reading-hub.service` · Windows Startup folder `paper-reading-hub.cmd` |

**Needs**: Python ≥ 3.9 and Node.js ≥ 18 (say which are present / missing, with the install command you would use). Zotero is not required. Internet only for the one-time pip + KaTeX download.

**Things to know / risks**:
- A background web service runs on `http://127.0.0.1:<port>/` (local machine only, ~10–20 MB RAM). It serves the files under the data root to programs on this computer — don't pick a folder that holds secrets.
- With autostart it starts at every login; without autostart the agent starts it when needed.
- Each report is expensive: the agent reads every page as text and as an image; expect a long run and many tokens per paper.
- Reports quote and crop the paper for personal study; don't publish them.
- Nothing outside the locations above is changed; the system Python is not modified (everything goes into a venv). Uninstall anytime (see the end).

**Questions** (offer defaults):
1. Install for which agent(s)? (default: the one you are)
2. Data root — where reports, PDFs and notes live? Default `~/Papers` (Windows `%USERPROFILE%\Papers`). Any folder is fine, including an existing literature folder.
3. Start the reading hub automatically at login? (`yes` recommended if they will read often; `no` otherwise)
4. Only if 8614 is taken: which port? (e.g. 8615)
5. Optional now (otherwise asked before the first report): a sentence about their background, field and why they read papers, so reports are pitched to them.
6. If Python or Node is missing: may you install it with the command you showed? (Otherwise give them the link and stop.)

## Step 3 — Install (after the user agreed)

1. **Missing prerequisites** (only with permission): macOS `brew install node` / `brew install python`; Debian/Ubuntu `sudo apt install nodejs python3 python3-venv` (Node must be ≥ 18 — use NodeSource or nvm if the distro's is older); Windows `winget install OpenJS.NodeJS.LTS` / `winget install Python.Python.3.12`. If you cannot run them (sudo/admin), give the commands to the user and wait.
2. **Skill files** → put this repository at the skill location for each chosen agent (folder name `paper-reading`):
   - If git is available: `git clone --depth 1 https://github.com/Hessure03/paper-reading-skill.git <skill location>`
   - Otherwise download `https://github.com/Hessure03/paper-reading-skill/archive/refs/heads/main.zip`, unzip, and move the inner folder to `<skill location>`.
   - Both agents: clone once, then copy (or symlink on macOS/Linux) the folder to the second location.
   - If the location already exists: ask before replacing it; `git -C <location> pull` updates a clone.
3. **Engine**: `python3 <skill location>/engine/install.py --check` (Windows: `py -3 …` or `python …`), then
   `python3 <skill location>/engine/install.py --root "<data root>" --autostart yes|no [--port N]`.
   Show the user the output. If it fails, read the message, fix the cause (missing venv module, port taken, no network) and re-run; it is safe to re-run.
4. **Reader profile** (if given): edit `~/.config/paper-reading/config.json` → `profile` = `{"background": "…", "field": "…", "goal": "…"}`; keep all other keys.

## Step 4 — Check and hand over

1. `<config python> <engine>/hubctl.py status` must say it is running; open `http://127.0.0.1:<port>/` if you have a browser tool (an empty hub page is expected).
2. Tell the user, briefly:
   - Where everything was installed (the real paths) and whether autostart is on.
   - How to use: "对我说：**精读这篇论文 /path/to/paper.pdf**"（也可以给 arXiv 链接或 Zotero 条目）. The hub is at `http://127.0.0.1:<port>/`; `engine/使用说明.md` in the data root explains highlighting and notes.
   - They may need to restart the agent (or open a new session) for the skill to appear.
   - Update: `git -C <skill location> pull` then re-run `install.py` (no arguments needed).
   - Uninstall: `<python> <data root>/_paper-reading/engine/uninstall.py` stops the service and removes the login item (add `--remove-engine` to delete the engine and config); then delete the skill folder. Their reports, PDFs and notes are never deleted by these scripts.
