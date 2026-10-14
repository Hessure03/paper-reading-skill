#!/usr/bin/env python3
"""端到端冒烟测试：安装 → 造一份 3 页 PDF → new_paper --pdf → pdftool 各子命令 → 构建 → 主页读写笔记 → 卸载。
用法：python3 tests/smoke_test.py <临时目录> [--autostart yes|no] [--port 8698]
会写 ~/.config/paper-reading/config.json；在自己电脑上运行前可以把 HOME（Windows 为 USERPROFILE）指向临时目录。
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmp = os.path.abspath(sys.argv[1])
autostart = sys.argv[sys.argv.index("--autostart") + 1] if "--autostart" in sys.argv else "no"
port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8698
root = os.path.join(tmp, "Papers dir 论文")  # 故意带空格和中文
os.makedirs(tmp, exist_ok=True)


def run(cmd, **kw):
    print("$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", **kw)
    print(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit(f"FAILED ({r.returncode}): {cmd}")
    return r.stdout


def http(method, url, body=None, headers=None):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read()


run([sys.executable, os.path.join(SKILL, "engine", "install.py"), "--root", root, "--port", str(port), "--autostart", autostart])
cfg = json.load(open(os.path.join(os.path.expanduser("~"), ".config", "paper-reading", "config.json"), encoding="utf-8"))
PY, E, NODE = cfg["python"], cfg["engine"], cfg["node"] or "node"

pdf = os.path.join(tmp, "sample paper.pdf")
run([PY, "-c", f"""
import fitz
doc = fitz.open()
for i in range(3):
    p = doc.new_page()
    p.insert_text((72, 80), f"Sample Paper page {{i+1}}: tactile sensing improves retrieval by 35 percent.", fontsize=11)
    if i == 1:
        p.draw_rect(fitz.Rect(100, 150, 400, 300), color=(0, 0, 1), fill=(0.8, 0.9, 1))
        p.insert_text((100, 320), "Fig. 1: A blue box standing in for a figure.", fontsize=10)
doc.save({pdf!r})
"""])

ID = "Smoke2026-SamplePaper"
run([PY, os.path.join(E, "new_paper.py"), ID, "reports/Smoke_2026_Sample.html", "--pdf", pdf])
D = os.path.join(cfg["data"], ID)
src = os.path.join(D, "source.pdf")
assert "总页数：3" in run([PY, os.path.join(E, "pdftool.py"), "info", src])
run([PY, os.path.join(E, "pdftool.py"), "render", src, os.path.join(tmp, "read"), "60"])
assert os.path.exists(os.path.join(tmp, "read", "p-03.jpg"))
assert "35 percent" in run([PY, os.path.join(E, "pdftool.py"), "text", src, "1"])
assert "◆图注" in run([PY, os.path.join(E, "pdftool.py"), "find", src, "2"])
run([PY, os.path.join(E, "pdftool.py"), "crop", src, "2", "90", "140", "320", "170", os.path.join(D, "figs", "fig1.webp")])

pj = os.path.join(D, "paper.json")
meta = json.load(open(pj, encoding="utf-8"))
meta.update({"short": "Smoke 2026", "title": "Sample Paper", "titleZh": "示例论文", "authors": ["A. Tester"],
             "venue": "Test 2026", "year": 2026, "pages": 3, "tags": ["测试"]})
meta["card"] = {k: "测试 [p.1]" for k in meta["card"]}
json.dump(meta, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
with open(os.path.join(D, "src", "01_all.txt"), "w", encoding="utf-8") as f:
    f.write("""## 全文
@@ overview | 一页速览 | p.1
直: 用手摸着找东西。
原: [p.1] Sample Paper page 1: tactile sensing improves retrieval by 35 percent.
式: r = r_t + r_o
@@ figure | 插图 | p.2-3
图: figs/fig1.webp | **Fig.1** 一个蓝色方框。[p.2]
数: 提升 **35%** [p.1]
""")
out = run([NODE, os.path.join(E, "build.js"), ID])
assert "页码覆盖：3/3" in out, out
report = os.path.join(root, "reports", "Smoke_2026_Sample.html")
html = open(report, encoding="utf-8").read()
assert "source.pdf#page=2" in html and "zotero://" not in html

hub = f"http://127.0.0.1:{port}"
assert http("GET", hub + "/")[0] == 200
assert http("GET", hub + "/reports/Smoke_2026_Sample.html")[0] == 200
assert http("GET", hub + f"/_paper-reading/data/{ID}/source.pdf")[0] == 200
state = {"state": {"v": 1, "notes": {"overview": {"text": "?? 测试"}}, "flags": {}, "done": {}, "hls": [], "imgs": {}},
         "markdown": "# 测试"}
code, body = http("PUT", hub + f"/api/state?doc={ID}", json.dumps(state).encode("utf-8"),
                  {"X-Paper": "1", "Content-Type": "application/json", "Host": f"127.0.0.1:{port}"})
assert code == 200 and json.loads(body)["ok"], body
assert os.path.exists(os.path.join(D, "notes", "summary.md"))
try:
    http("PUT", hub + f"/api/state?doc={ID}", b"{}", {"Content-Type": "application/json"})
    sys.exit("write without X-Paper was accepted")
except urllib.error.HTTPError as e:
    assert e.code == 403

run([sys.executable, os.path.join(E, "uninstall.py")])
r = subprocess.run([PY, os.path.join(E, "hubctl.py"), "status"], capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 1, r.stdout
assert os.path.exists(os.path.join(D, "notes", "data.json")) and os.path.exists(report)
print("✓ 冒烟测试全部通过")
