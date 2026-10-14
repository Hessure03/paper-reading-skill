#!/usr/bin/env python3
"""模板或引擎更新后，重新构建 data/ 下所有论文的报告（笔记不受影响）。用法：python rebuild_all.py"""
import json
import os
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

ENGINE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(ENGINE), "data")
try:
    node = json.load(open(os.path.join(ENGINE, "settings.json"), encoding="utf-8")).get("node")
except Exception:  # noqa: BLE001
    node = None
node = node if node and os.path.exists(node) else shutil.which("node")
if not node:
    sys.exit("找不到 node")
fail = 0
for pid in sorted(os.listdir(DATA)) if os.path.isdir(DATA) else []:
    d = os.path.join(DATA, pid)
    if os.path.isfile(os.path.join(d, "paper.json")):
        fail |= subprocess.run([node, os.path.join(ENGINE, "build.js"), d]).returncode
sys.exit(1 if fail else 0)
