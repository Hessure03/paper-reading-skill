#!/usr/bin/env python3
"""安装 / 更新精读系统（macOS、Linux、Windows）。只用 Python 标准库，从 skill 的 engine/ 目录运行：

  python3 install.py --check                         只检查环境，什么都不改
  python3 install.py --root <数据根目录> [--port 8614] [--autostart yes|no]

它会做的事（全部在下面列出的位置，不碰其他文件）：
  1. 把引擎复制到 <根目录>/_paper-reading/engine/，建 <根目录>/_paper-reading/data/
  2. 在 engine/.venv 建独立的 Python 虚拟环境，装 PyMuPDF、Pillow（不动系统 Python）
  3. 从 npm 官方源下载 KaTeX 0.16.11，校验 sha512 后放进 engine/vendor/katex/
  4. 写 ~/.config/paper-reading/config.json（记录根目录、端口、Python 路径、读者背景）
  5. 启动本机网页服务 http://127.0.0.1:<端口>/ （只监听 127.0.0.1）
     --autostart yes：注册登录自启（macOS launchd / Linux systemd 用户服务 / Windows 启动文件夹）
     --autostart no ：只在本次启动；以后由助手在需要时启动
重复运行即可更新引擎，不会动任何报告、数据或笔记。卸载：python <根目录>/_paper-reading/engine/uninstall.py
"""
import argparse
import base64
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
CONFIG = os.path.join(HOME, ".config", "paper-reading", "config.json")
SYSTEM = platform.system()  # Darwin / Linux / Windows
KATEX_VER = "0.16.11"
KATEX_URL = f"https://registry.npmjs.org/katex/-/katex-{KATEX_VER}.tgz"
KATEX_SHA512 = "RQrI8rlHY92OLf3rho/Ts8i/XvjgguEjOkO1BEXcU3N8BqPpSzBNwV/G0Ukr+P/l3ivvJUE/Fa/CwbS6HesGNQ=="
PIP_PKGS = ["PyMuPDF>=1.24,<2", "Pillow>=10,<12"]
ENGINE_FILES = ["server.py", "build.js", "template.html", "pdftool.py", "new_paper.py", "rebuild_all.py",
                "uninstall.py", "hubctl.py", "使用说明.md"]
LABEL = "io.github.paper-reading.hub"
UNIT = "paper-reading-hub.service"
WIN_STARTUP = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
                           "paper-reading-hub.cmd")


def venv_python(engine, windowed=False):
    if SYSTEM == "Windows":
        return os.path.join(engine, ".venv", "Scripts", "pythonw.exe" if windowed else "python.exe")
    return os.path.join(engine, ".venv", "bin", "python")


def node_version():
    node = shutil.which("node")
    if not node:
        return None, None
    try:
        v = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
        return node, v
    except Exception:  # noqa: BLE001
        return node, None


def hint(name):
    return {
        "node": {"Darwin": "brew install node（或到 https://nodejs.org 下载 LTS）",
                 "Linux": "用发行版包管理器装 nodejs ≥ 18（如 sudo apt install nodejs），或用 nvm",
                 "Windows": "winget install OpenJS.NodeJS.LTS（或到 https://nodejs.org 下载 LTS）"},
        "python": {"Darwin": "brew install python（或到 https://www.python.org 下载）",
                   "Linux": "sudo apt install python3 python3-venv（其他发行版用对应包管理器）",
                   "Windows": "winget install Python.Python.3.12（或到 https://www.python.org 下载，勾选 Add to PATH）"},
    }[name].get(SYSTEM, "")


def check():
    """返回 (ok, 报告行)。"""
    lines, ok = [], True
    py = sys.version_info
    if py >= (3, 9):
        lines.append(f"✓ Python {py.major}.{py.minor}.{py.micro}（{sys.executable}）")
    else:
        ok = False
        lines.append(f"✗ Python 需要 ≥ 3.9，当前 {py.major}.{py.minor}。安装：{hint('python')}")
    try:
        import venv  # noqa: F401
        import ensurepip  # noqa: F401
        lines.append("✓ Python venv 模块可用")
    except ImportError:
        ok = False
        lines.append("✗ 缺少 venv/ensurepip 模块（Debian/Ubuntu：sudo apt install python3-venv）")
    node, v = node_version()
    if node and v and int(v.lstrip("v").split(".")[0]) >= 18:
        lines.append(f"✓ Node.js {v}（{node}）")
    else:
        ok = False
        lines.append(f"✗ 需要 Node.js ≥ 18（当前：{v or '未找到'}）。安装：{hint('node')}")
    lines.append(f"· 系统：{SYSTEM} {platform.release()}；自启方式：" +
                 {"Darwin": "launchd 登录项", "Linux": "systemd 用户服务", "Windows": "启动文件夹里的 .cmd"}.get(SYSTEM, "不支持，只能手动启动"))
    if os.path.exists(CONFIG):
        try:
            cfg = json.load(open(CONFIG, encoding="utf-8"))
            lines.append(f"· 已安装过：根目录 {cfg.get('root')}，端口 {cfg.get('port')}，自启 {cfg.get('autostart')}")
        except Exception:  # noqa: BLE001
            lines.append(f"· {CONFIG} 存在但无法读取")
    else:
        lines.append("· 还没有安装过")
    return ok, lines


def run(cmd, **kw):
    print("  $ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def setup_venv(engine):
    py = venv_python(engine)
    if not os.path.exists(py):
        print("建立 Python 虚拟环境 engine/.venv …")
        run([sys.executable, "-m", "venv", os.path.join(engine, ".venv")])
    probe = subprocess.run([py, "-c", "import fitz, PIL"], capture_output=True)
    if probe.returncode != 0:
        print("安装 PyMuPDF、Pillow（约 30–60 MB，只装进 engine/.venv）…")
        run([py, "-m", "pip", "install", "--disable-pip-version-check", "-q"] + PIP_PKGS)
    return py


def setup_katex(engine):
    dest = os.path.join(engine, "vendor", "katex")
    if os.path.exists(os.path.join(dest, "katex.min.js")):
        return
    print(f"下载 KaTeX {KATEX_VER}（npm 官方源，约 1.5 MB，校验 sha512）…")
    with urllib.request.urlopen(KATEX_URL, timeout=60) as r:
        blob = r.read()
    if base64.b64encode(hashlib.sha512(blob).digest()).decode() != KATEX_SHA512:
        sys.exit("✗ KaTeX 校验失败，已放弃（没有写入任何文件）")
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile() or not m.name.startswith("package/dist/"):
                continue
            rel = m.name[len("package/dist/"):]
            if ".." in rel.split("/") or rel.endswith(".mjs") or rel in ("katex.js", "katex.css", "README.md"):
                continue
            out = os.path.join(dest, *rel.split("/"))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(tf.extractfile(m).read())


def ping(port, tries=10):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/_ping.gif", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
    return False


def autostart_on(engine, port):
    server = os.path.join(engine, "server.py")
    log = os.path.join(engine, "logs", "server.log")
    if SYSTEM == "Darwin":
        plist = os.path.join(HOME, "Library", "LaunchAgents", LABEL + ".plist")
        os.makedirs(os.path.dirname(plist), exist_ok=True)
        x = lambda s: s.replace("&", "&amp;").replace("<", "&lt;")  # noqa: E731
        with open(plist, "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key><array><string>{x(venv_python(engine))}</string><string>{x(server)}</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>{x(log)}</string>
  <key>StandardErrorPath</key><string>{x(log)}</string>
</dict></plist>
""")
        uid = str(os.getuid())
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True)
        run(["launchctl", "bootstrap", f"gui/{uid}", plist])
        return f"launchd 登录项 {plist}"
    if SYSTEM == "Linux":
        if not shutil.which("systemctl") or subprocess.run(["systemctl", "--user", "show-environment"],
                                                           capture_output=True).returncode != 0:
            return None
        unit_dir = os.path.join(HOME, ".config", "systemd", "user")
        os.makedirs(unit_dir, exist_ok=True)
        unit = os.path.join(unit_dir, UNIT)
        with open(unit, "w", encoding="utf-8") as f:
            f.write(f"""[Unit]
Description=Paper reading hub (127.0.0.1:{port})

[Service]
ExecStart="{venv_python(engine)}" "{server}"
Restart=on-failure

[Install]
WantedBy=default.target
""")
        run(["systemctl", "--user", "daemon-reload"])
        run(["systemctl", "--user", "enable", UNIT])
        run(["systemctl", "--user", "restart", UNIT])
        return f"systemd 用户服务 {unit}"
    if SYSTEM == "Windows":
        os.makedirs(os.path.dirname(WIN_STARTUP), exist_ok=True)
        with open(WIN_STARTUP, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\nchcp 65001 >nul\r\nstart "" "{venv_python(engine, True)}" "{server}"\r\n')
        subprocess.run([venv_python(engine), os.path.join(engine, "hubctl.py"), "restart"], check=False)
        return f"启动文件夹 {WIN_STARTUP}"
    return None


def main():
    ap = argparse.ArgumentParser(description="安装 / 更新精读系统")
    ap.add_argument("--check", action="store_true", help="只检查环境")
    ap.add_argument("--root", help="数据根目录（报告和笔记放这里）")
    ap.add_argument("--port", type=int, help="本机服务端口，默认 8614")
    ap.add_argument("--autostart", choices=["yes", "no"], help="是否登录自启")
    args = ap.parse_args()

    ok, lines = check()
    print("\n".join(lines))
    if args.check:
        sys.exit(0 if ok else 1)
    if not ok:
        sys.exit("\n请先装好上面标 ✗ 的组件，再重新运行。")

    old = {}
    if os.path.exists(CONFIG):
        try:
            old = json.load(open(CONFIG, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            old = {}
    root = args.root or old.get("root")
    if not root:
        sys.exit("请用 --root 指定数据根目录（例如 --root ~/Papers）")
    root = os.path.abspath(os.path.expanduser(root))
    port = args.port or old.get("port") or 8614
    autostart = args.autostart or old.get("autostart") or "no"
    if old.get("root") and os.path.abspath(old["root"]) != root:
        print(f"⚠ 之前装在 {old['root']}，这次换成 {root}。旧位置的数据不会被移动或删除。")

    sysdir = os.path.join(root, "_paper-reading")
    engine = os.path.join(sysdir, "engine")
    for d in (engine, os.path.join(engine, "logs"), os.path.join(sysdir, "data")):
        os.makedirs(d, exist_ok=True)
    for f in ENGINE_FILES:
        shutil.copy2(os.path.join(HERE, f), os.path.join(engine, f))
    shutil.copy2(os.path.join(HERE, "使用说明.md"), os.path.join(sysdir, "使用说明.md"))
    print(f"引擎已复制到 {engine}")

    py = setup_venv(engine)
    setup_katex(engine)
    node, _ = node_version()
    settings = {"port": port, "python": py, "node": node}
    with open(os.path.join(engine, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    cfg = dict(old)
    cfg.update({"root": root, "engine": engine, "data": os.path.join(sysdir, "data"), "python": py, "node": node,
                "port": port, "autostart": autostart, "hub": f"http://127.0.0.1:{port}/"})
    cfg.setdefault("reportsDir", "reports")
    cfg.setdefault("profile", {"background": "", "field": "", "goal": ""})
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"配置已写入 {CONFIG}")

    # 先停掉旧的（端口或自启方式可能变了），再按选择启动
    subprocess.run([sys.executable, os.path.join(engine, "uninstall.py"), "--stop-only", "--quiet"], check=False)
    how = autostart_on(engine, port) if autostart == "yes" else None
    if autostart == "yes" and not how:
        print("⚠ 这个系统上无法注册自启（例如 WSL 或没有 systemd），改为本次手动启动。")
        cfg["autostart"] = "no"
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    if not how:
        subprocess.run([py, os.path.join(engine, "hubctl.py"), "start"], check=False)
    if ping(port):
        print(f"✓ 精读主页已运行：http://127.0.0.1:{port}/" + (f"（自启：{how}）" if how else "（未设自启，重启电脑后由助手或 hubctl.py start 启动）"))
    else:
        sys.exit(f"⚠ 服务没有响应，请查看 {os.path.join(engine, 'logs', 'server.log')}（端口 {port} 可能被占用，可用 --port 换一个）")


if __name__ == "__main__":
    main()
