#!/usr/bin/env python3
"""停止精读主页服务并取消登录自启（任何系统通用，只用标准库）。
  python uninstall.py                    停止服务、取消自启；保留引擎、报告、数据和笔记
  python uninstall.py --remove-engine    另外删除 engine/ 文件夹（含 .venv 和 KaTeX）与 ~/.config/paper-reading/
永远不会删除 data/（讲解源文件和你的笔记）和任何报告 .html。skill 本身的文件夹请自己删除。
"""
import os
import platform
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:  # noqa: BLE001
        pass

ENGINE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
SYSTEM = platform.system()
LABEL = "io.github.paper-reading.hub"
UNIT = "paper-reading-hub.service"
WIN_STARTUP = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
                           "paper-reading-hub.cmd")
quiet = "--quiet" in sys.argv


def say(msg):
    if not quiet:
        print(msg)


def main():
    if SYSTEM == "Darwin":
        plist = os.path.join(HOME, "Library", "LaunchAgents", LABEL + ".plist")
        r = subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"], capture_output=True)
        if r.returncode == 0:
            say(f"已停止 launchd 服务 {LABEL}")
        if "--stop-only" not in sys.argv and os.path.exists(plist):
            os.remove(plist)
            say(f"已删除登录项 {plist}")
    elif SYSTEM == "Linux" and shutil.which("systemctl"):
        unit = os.path.join(HOME, ".config", "systemd", "user", UNIT)
        if os.path.exists(unit):
            subprocess.run(["systemctl", "--user", "stop", UNIT], capture_output=True)
            say(f"已停止 systemd 用户服务 {UNIT}")
            if "--stop-only" not in sys.argv:
                subprocess.run(["systemctl", "--user", "disable", UNIT], capture_output=True)
                os.remove(unit)
                subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
                say(f"已删除 {unit}")
    elif SYSTEM == "Windows" and "--stop-only" not in sys.argv and os.path.exists(WIN_STARTUP):
        os.remove(WIN_STARTUP)
        say(f"已删除启动项 {WIN_STARTUP}")
    # 由 hubctl.py / Windows 启动项启动的进程
    if os.path.exists(os.path.join(ENGINE, "settings.json")):
        subprocess.run([sys.executable, os.path.join(ENGINE, "hubctl.py"), "stop"], capture_output=quiet)
    if "--remove-engine" in sys.argv:
        cfg = os.path.join(HOME, ".config", "paper-reading")
        shutil.rmtree(cfg, ignore_errors=True)
        say(f"已删除 {cfg}")
        say(f"正在删除 {ENGINE}（data/ 和报告保留）")
        shutil.rmtree(ENGINE, ignore_errors=True)
    elif "--stop-only" not in sys.argv:
        say("引擎、报告、数据和笔记都保留。重新运行 skill 里的 engine/install.py 可恢复。")


if __name__ == "__main__":
    main()
