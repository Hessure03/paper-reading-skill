#!/usr/bin/env python3
"""精读主页服务器（paper hub）—— 只用 Python 标准库。

由 install.py 注册为登录自启（或由 hubctl.py 启动），只监听本机 127.0.0.1。macOS / Linux / Windows 通用。
目录约定（ROOT 是安装时选的数据根目录）：
  ROOT/<文件夹>/.../<报告>.html             精读报告（每篇一个文件，位置由 paper.json 的 out 决定）
  ROOT/_paper-reading/engine/             本文件、build.js、template.html、settings.json、vendor/katex、.venv
  ROOT/_paper-reading/data/<论文ID>/      paper.json、source.pdf、src/、figs/、demos/、notes/
  * http://127.0.0.1:<端口>/ 是"精读主页"，按文件夹列出 data/ 下所有论文；
  * 报告通过本服务打开时，笔记 / 高亮 / 图片保存在 data/<论文ID>/notes/：
      data.json        全部数据（每次保存覆盖更新）
      summary.md       可读的 Markdown 笔记汇总（助手答疑时读它）
      img/             粘贴的图片（删除后自动清理文件）
      backup/          每天一份备份，保留最近 30 天
"""
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

TOOLS = os.path.dirname(os.path.abspath(__file__))
SYS = os.path.dirname(TOOLS)
ROOT = os.path.dirname(SYS)
DATA = os.path.join(SYS, "data")
try:
    _SETTINGS = json.load(open(os.path.join(TOOLS, "settings.json"), encoding="utf-8"))
except Exception:  # noqa: BLE001
    _SETTINGS = {}
PORT = int(os.environ.get("PAPER_HUB_PORT") or _SETTINGS.get("port") or 8614)
PIDFILE = os.path.join(TOOLS, "logs", "server.pid")
HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
MAX_BODY = 30 * 1024 * 1024
KEEP_BACKUPS = 30
IMG_GRACE = 600  # 秒：新上传但尚未写入 data.json 的图片不清理
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}")
GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"


def atomic_write(path, data: bytes):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def resolve_doc(doc: str):
    """论文 ID → 数据/<ID> 目录（必须含 paper.json）；不合法返回 None。"""
    doc = (doc or "").strip()
    if not ID_RE.fullmatch(doc):
        return None
    path = os.path.join(DATA, doc)
    return path if os.path.isfile(os.path.join(path, "paper.json")) else None


def daily_backup(notes):
    data = os.path.join(notes, "data.json")
    if not os.path.exists(data):
        return
    bdir = os.path.join(notes, "backup")
    os.makedirs(bdir, exist_ok=True)
    target = os.path.join(bdir, "data-" + datetime.date.today().isoformat() + ".json")
    with open(data, "rb") as f:
        atomic_write(target, f.read())
    files = sorted(n for n in os.listdir(bdir) if n.startswith("data-"))
    for old in files[:-KEEP_BACKUPS]:
        os.remove(os.path.join(bdir, old))


def gc_images(notes, state_text):
    idir = os.path.join(notes, "img")
    if not os.path.isdir(idir):
        return
    now = time.time()
    for name in os.listdir(idir):
        if ("/img/" + name) in state_text:
            continue
        p = os.path.join(idir, name)
        if now - os.path.getmtime(p) > IMG_GRACE:
            os.remove(p)


def paper_stats(d):
    """读取笔记，统计读懂的小节、笔记条数、未解决的疑问。"""
    out = {"done": 0, "notes": 0, "qs": 0, "last": None}
    data = os.path.join(d, "notes", "data.json")
    if not os.path.exists(data):
        return out
    try:
        st = json.load(open(data, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return out
    out["done"] = len(st.get("done", {}))
    notes = st.get("notes", {})
    hls = st.get("hls", [])
    out["notes"] = len(notes) + len([h for h in hls if h.get("note")])
    qs = sum(1 for h in hls if h.get("c") == 3)
    qs += sum(1 for n in notes.values() for line in (n.get("text") or "").split("\n") if line.strip().startswith("??"))
    qs += sum(1 for f in st.get("flags", {}).values() if f.get("q"))
    out["qs"] = qs
    out["last"] = os.path.getmtime(data)
    return out


def hub_html():
    groups = {}
    try:
        ids = sorted(e.name for e in os.scandir(DATA) if e.is_dir() and not e.name.startswith((".", "_")))
    except OSError:
        ids = []
    for pid in ids:
        d = os.path.join(DATA, pid)
        try:
            meta = json.load(open(os.path.join(d, "paper.json"), encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        out = meta.get("out", "")
        stage = out.split("/")[0] if "/" in out else "（根目录）"
        st = paper_stats(d)
        total = meta.get("sections") or 0
        pct = int(100 * st["done"] / total) if total else 0
        exists = bool(out) and os.path.isfile(os.path.join(ROOT, out))
        url = "/" + urllib.parse.quote(out) if exists else ""
        status = "未开始" if not st["last"] else ("读完" if total and st["done"] >= total else "在读")
        when = datetime.datetime.fromtimestamp(st["last"]).strftime("%m-%d %H:%M") if st["last"] else "还没有笔记"
        tags = "".join(f"<span class=tag>{html.escape(t)}</span>" for t in meta.get("tags", []))
        venue = meta.get("venue") or ""
        if meta.get("year") and str(meta["year"]) not in venue:
            venue = " · ".join(x for x in [venue, str(meta["year"])] if x)
        search = " ".join(str(x) for x in [meta.get("title"), meta.get("titleZh"), venue, " ".join(meta.get("tags", [])), " ".join(meta.get("authors", [])[:3]), status]).lower()
        warn = "" if exists else "<small class=warn>报告文件不存在，需要重新构建</small>"
        q = f" · <b class=q>疑问 {st['qs']}</b>" if st["qs"] else ""
        card = (f'<a class="card st-{status}" {"href=" + chr(34) + url + chr(34) if url else ""} data-s="{html.escape(search)}">'
                f'<span class=row><span class=venue>{html.escape(venue)}</span><span class=status>{status}</span></span>'
                f'<b>{html.escape(meta.get("title", pid))}</b>'
                f'<small>{html.escape(meta.get("titleZh", ""))}</small><span class=tags>{tags}</span>'
                f'<span class=bar><i style="width:{pct}%"></i></span>'
                f'<small>读懂 {st["done"]}/{total} 节 · 笔记 {st["notes"]} 条{q} · {when}</small>{warn}</a>')
        groups.setdefault(stage, []).append(card)
    body = "".join(f"<h2>{html.escape(g)}<span>{len(c)} 篇</span></h2><div class=grid>{''.join(c)}</div>" for g, c in groups.items()) \
        or "<p>还没有精读报告。</p>"
    return f"""<!doctype html><html lang=zh-CN><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>精读主页</title><style>
:root{{--bg:#f6f4ef;--paper:#fff;--ink:#1f2328;--ink2:#57606a;--line:#e3ded3;--accent:#2f5d8a;--ok:#3f8f4f;--warn:#c0392b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181c;--paper:#1e2126;--ink:#e6e6e6;--ink2:#a0a7b0;--line:#30343b;--accent:#7fb0e0;--ok:#5fae6c;--warn:#e07a6e}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"PingFang SC",sans-serif;padding:24px 16px 60px}}
main{{max-width:1100px;margin:0 auto}}h1{{font-size:24px;margin:0 0 4px}}
h2{{font-size:16px;color:var(--ink2);margin:26px 0 10px}}h2 span{{font-weight:400;font-size:13px;margin-left:8px}}
.top{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}}
#f{{border:1px solid var(--line);border-radius:8px;padding:6px 10px;background:var(--paper);color:var(--ink);font-size:14px;width:min(320px,100%)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
.card{{display:flex;flex-direction:column;gap:4px;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-decoration:none;color:inherit;min-width:0}}
a.card[href]:hover{{border-color:var(--accent)}}.card small{{color:var(--ink2)}}.card b{{line-height:1.4}}
.row{{display:flex;justify-content:space-between;gap:8px;font-size:12px}}.venue{{color:var(--accent);font-weight:600}}
.status{{border-radius:10px;padding:0 8px;background:var(--bg);color:var(--ink2)}}.st-在读 .status{{background:var(--accent);color:var(--paper)}}.st-读完 .status{{background:var(--ok);color:var(--paper)}}
.tags{{display:flex;flex-wrap:wrap;gap:4px}}.tag{{font-size:12px;border:1px solid var(--line);border-radius:10px;padding:0 7px;color:var(--ink2)}}
.bar{{height:5px;background:var(--line);border-radius:3px;overflow:hidden}}.bar i{{display:block;height:100%;background:var(--ok)}}
.q{{color:var(--warn);font-weight:600}}.warn{{color:var(--warn)!important}}.hide{{display:none}}
</style></head><body><main><div class=top><div><h1>精读主页</h1><div style="color:var(--ink2);font-size:13px">{html.escape(ROOT)} · 笔记自动保存在 _paper-reading/data/</div></div>
<input id=f type=search placeholder="筛选：标题、会议、标签、状态…" autocomplete=off></div>{body}</main>
<script>
const f=document.getElementById('f');f.addEventListener('input',()=>{{const q=f.value.trim().toLowerCase();
document.querySelectorAll('.card').forEach(c=>c.classList.toggle('hide',!!q&&!q.split(/\\s+/).every(w=>c.dataset.s.includes(w))));
document.querySelectorAll('.grid').forEach(g=>{{g.previousElementSibling.classList.toggle('hide',!g.querySelector('.card:not(.hide)'))}});}});
</script></body></html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):  # 安静运行，日志不增长
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send(self, code, body: bytes, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _guard(self):
        """拒绝来自其他网站的写请求（DNS rebinding / CSRF）。"""
        if self.headers.get("Host") not in HOSTS:
            return False
        origin = self.headers.get("Origin")
        if origin and origin.split("//", 1)[-1] not in HOSTS:
            return False
        return self.headers.get("X-Paper") == "1"

    def _parts(self):
        path, _, query = self.path.partition("?")
        return urllib.parse.unquote(path), urllib.parse.parse_qs(query)

    def do_GET(self):
        path, q = self._parts()
        if self.headers.get("Host") not in HOSTS:
            return self._send(403, b"forbidden", "text/plain")
        if path in ("/", "/index.html"):
            return self._send(200, hub_html().encode("utf-8"), "text/html; charset=utf-8")
        if path == "/_ping.gif":
            return self._send(200, GIF, "image/gif")
        if path == "/api/state":
            d = resolve_doc(q.get("doc", [""])[0])
            if not d:
                return self._json(404, {"ok": False, "error": "unknown doc"})
            data = os.path.join(d, "notes", "data.json")
            raw = open(data, "rb").read() if os.path.exists(data) else b"{}"
            return self._send(200, raw, "application/json; charset=utf-8")
        return super().do_GET()

    def do_PUT(self):
        path, q = self._parts()
        if path != "/api/state" or not self._guard():
            return self._json(403, {"ok": False})
        d = resolve_doc(q.get("doc", [""])[0])
        if not d:
            return self._json(404, {"ok": False, "error": "unknown doc"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("too large")
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            notes = os.path.join(d, "notes")
            os.makedirs(notes, exist_ok=True)
            daily_backup(notes)
            text = json.dumps(payload["state"], ensure_ascii=False, indent=1)
            atomic_write(os.path.join(notes, "data.json"), text.encode("utf-8"))
            if isinstance(payload.get("markdown"), str):
                atomic_write(os.path.join(notes, "summary.md"), payload["markdown"].encode("utf-8"))
            gc_images(notes, text)
            self._json(200, {"ok": True, "t": time.time()})
        except Exception as e:  # noqa: BLE001
            self._json(400, {"ok": False, "error": str(e)})

    def do_POST(self):
        path, q = self._parts()
        if path != "/api/img" or not self._guard():
            return self._json(403, {"ok": False})
        doc = q.get("doc", [""])[0]
        d = resolve_doc(doc)
        name = q.get("name", [""])[0]
        if not d or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.(png|jpg|jpeg|gif|webp)", name):
            return self._json(400, {"ok": False, "error": "bad doc or name"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("too large")
            idir = os.path.join(d, "notes", "img")
            os.makedirs(idir, exist_ok=True)
            atomic_write(os.path.join(idir, name), self.rfile.read(n))
            rel = os.path.relpath(os.path.join(idir, name), ROOT).replace(os.sep, "/")
            self._json(200, {"ok": True, "src": "/" + urllib.parse.quote(rel)})
        except Exception as e:  # noqa: BLE001
            self._json(400, {"ok": False, "error": str(e)})


def main():
    url = f"http://127.0.0.1:{PORT}/"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"端口 {PORT} 已被占用（精读主页可能已在运行）：{url}")
        if "--open" in sys.argv:
            webbrowser.open(url)
        return
    print(f"精读主页：{url}  （根目录 {ROOT}）", flush=True)
    try:
        os.makedirs(os.path.dirname(PIDFILE), exist_ok=True)
        with open(PIDFILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    if "--open" in sys.argv:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
