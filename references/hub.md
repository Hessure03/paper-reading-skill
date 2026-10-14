# Paper hub: install, storage, troubleshooting

## Install / update
First install: follow `INSTALL.md` (ask the user first). Update after pulling a new skill version: `python3 <skill>/engine/install.py` (re-uses root, port and autostart from the config), then `PY E/rebuild_all.py`.
- Copies the engine to `ROOT/_paper-reading/engine/`, creates `ROOT/_paper-reading/data/`, makes `engine/.venv` with PyMuPDF + Pillow, downloads KaTeX 0.16.11 once (sha512-checked), writes `engine/settings.json` and `~/.config/paper-reading/config.json`, starts the hub.
- `--autostart yes` registers a login item: macOS `~/Library/LaunchAgents/io.github.paper-reading.hub.plist` (launchd, KeepAlive); Linux `~/.config/systemd/user/paper-reading-hub.service` (falls back to manual if there is no user systemd, e.g. WSL); Windows `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\paper-reading-hub.cmd` (pythonw, no window). `--autostart no`: nothing is registered; `PY E/hubctl.py start` starts it when needed.
- Change port: `install.py --port N`, then `rebuild_all.py` (the port is baked into reports' hub links).
- Uninstall: `python3 E/uninstall.py` (stops the service, removes the login item; keeps engine, reports, data, notes). `--remove-engine` also deletes `engine/` and `~/.config/paper-reading/`. Data and reports are never deleted by any script.

## Manual control
`PY E/hubctl.py status | start | stop | restart | open`. Logs: `E/logs/server.log`; pid: `E/logs/server.pid`.

## Storage
- Opened through the hub: `GET/PUT /api/state?doc=<ID>` (header `X-Paper: 1`) → `data/<ID>/notes/data.json` (atomic write), daily backup in `notes/backup/` (30 kept), `notes/summary.md` regenerated on every save; images via `POST /api/img` → `notes/img/` (unreferenced images deleted after 10 min).
- State: `{notes:{secKey:{text}}, flags:{secKey:{star|q|idea|use}}, done:{secKey}, hls:[{id, sec, b, s, e, quote, c, note}], imgs:{secKey:[{src}]}, last}`. Highlight colours: 1 重点, 2 懂了, 3 疑问, 4 概念. Note lines starting `??` are questions.
- Opened as `file://` (double-click): the page pings the hub; if there are no browser-stored notes for this paper it redirects to the hub URL automatically, otherwise it shows a banner asking to export → open via hub → import. Browser storage key `paper:<ID>`.
- Security: binds 127.0.0.1 only; rejects foreign Host headers, cross-origin writes and writes without `X-Paper`; doc IDs are validated and must have `paper.json`. It serves files under ROOT read-only to the local machine — don't choose a root that contains secrets.

## Facts for user questions
- ~10–20 MB RAM, ~0% CPU idle, no window. Reports are single files (~1.2 MB: KaTeX ~0.7 MB + figures), can be emailed; recipients see no notes, and page links to a local PDF only work on the author's machine.
- Clearing browser website data only affects file:// mode, not hub mode.
- Page links: with `zotero.pdf` they are `zotero://open-pdf/library/items/<KEY>?page=N` (browser asks once whether to open Zotero); otherwise a relative link to `data/<ID>/source.pdf#page=N`, opened in the browser's PDF viewer (Chrome, Edge, Firefox honour `#page`; Safari may open at page 1).
- Install as an app: Chrome/Edge "Install page as app" / Safari "File → Add to Dock" on the hub page.

## Troubleshooting
- Hub not responding: `PY E/hubctl.py status`; read `E/logs/server.log`; port busy → reinstall with `--port`. macOS: `launchctl print gui/$(id -u)/io.github.paper-reading.hub | head`; Linux: `systemctl --user status paper-reading-hub`.
- "保存失败": service stopped → `hubctl.py start`; unsaved state is kept in browser storage (`paper:<ID>-emergency`).
- Card shows "报告文件不存在": `out` changed or file deleted → rebuild.
- Highlights "未能定位" after an update: the quoted text changed or the section key was renamed; they remain in summary.md.
- `pdftool.py` says PyMuPDF missing: you ran it with the system Python; use `python` from the config.
