#!/usr/bin/env python3
"""手动控制精读主页服务（任何系统通用，只用标准库）：
  python hubctl.py status     是否在运行
  python hubctl.py start      后台启动（已在运行则什么都不做）
  python hubctl.py stop       停止由 start 启动的服务（登录自启的服务请用 uninstall.py）
  python hubctl.py restart
  python hubctl.py open       确保运行，并在浏览器打开主页
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser

ENGINE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = json.load(open(os.path.join(ENGINE, "settings.json"), encoding="utf-8"))
PORT = SETTINGS.get("port", 8614)
URL = f"http://127.0.0.1:{PORT}/"
PIDFILE = os.path.join(ENGINE, "logs", "server.pid")
LOG = os.path.join(ENGINE, "logs", "server.log")


def alive():
    try:
        with urllib.request.urlopen(URL + "_ping.gif", timeout=2) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def start():
    if alive():
        print(f"已在运行：{URL}")
        return True
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    server = os.path.join(ENGINE, "server.py")
    log = open(LOG, "ab")
    if os.name == "nt":
        py = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        py = py if os.path.exists(py) else sys.executable
        flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
        subprocess.Popen([py, server], stdout=log, stderr=log, stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    else:
        subprocess.Popen([sys.executable, server], stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(20):
        time.sleep(0.3)
        if alive():
            print(f"✓ 已启动：{URL}")
            return True
    print(f"⚠ 启动失败，请看 {LOG}")
    return False


def stop():
    if not os.path.exists(PIDFILE):
        print("没有找到 pid 文件（服务没有运行，或是由登录自启管理的）")
        return
    try:
        pid = int(open(PIDFILE).read().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"已停止（pid {pid}）")
    except (ValueError, ProcessLookupError, OSError):
        print("进程已不存在")
    try:
        os.remove(PIDFILE)
    except OSError:
        pass
    for _ in range(10):
        if not alive():
            return
        time.sleep(0.3)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(f"运行中：{URL}" if alive() else "没有运行")
        sys.exit(0 if alive() else 1)
    elif cmd == "start":
        sys.exit(0 if start() else 1)
    elif cmd == "stop":
        stop()
    elif cmd == "restart":
        stop()
        sys.exit(0 if start() else 1)
    elif cmd == "open":
        if start():
            webbrowser.open(URL)
    else:
        sys.exit(__doc__)
