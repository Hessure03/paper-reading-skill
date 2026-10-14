#!/usr/bin/env python3
"""新建一篇论文的数据文件夹：data/<ID>/{paper.json, src/, figs/, demos/[, source.pdf]}。
用法：python new_paper.py <ID> <out> [--pdf <原文 PDF 路径>]
  ID   用 <第一作者姓><年份>-<两三个英文词>，例如 Zhao2024-UnknownObjectRetrieval；只用字母、数字、- _ .
  out  报告路径，相对数据根目录，例如 reports/Zhao_2024_UnknownObjectRetrieval.html
  --pdf  没有 Zotero（或想让页码链接直接打开 PDF）时给出原文；会复制成 data/<ID>/source.pdf，
         报告里的出处页码就链接到这个 PDF 的对应页。
生成的 paper.json 是骨架，其余字段（标题、作者、会议、DOI、Zotero key、页数、标签、card）由助手填写。
"""
import json
import os
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

args = sys.argv[1:]
pdf = None
if "--pdf" in args:
    i = args.index("--pdf")
    pdf = args[i + 1] if i + 1 < len(args) else sys.exit("--pdf 后面要跟 PDF 路径")
    del args[i:i + 2]
if len(args) != 2:
    sys.exit(__doc__)
ID, OUT = args[0], args[1].replace("\\", "/")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}", ID):
    sys.exit("ID 只能用字母、数字和 - _ .")
if os.path.isabs(OUT) or re.match(r"^[A-Za-z]:", OUT) or ".." in OUT.split("/") or not OUT.endswith(".html"):
    sys.exit("out 必须是相对数据根目录的 .html 路径")
data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", ID)
if os.path.exists(os.path.join(data, "paper.json")):
    sys.exit(f"已存在：{data}")
if pdf and not os.path.isfile(pdf):
    sys.exit(f"找不到 PDF：{pdf}")
for sub in ("src", "figs", "demos"):
    os.makedirs(os.path.join(data, sub), exist_ok=True)
if pdf:
    shutil.copy2(pdf, os.path.join(data, "source.pdf"))
skel = {
    "id": ID, "out": OUT, "short": "", "title": "", "titleZh": "", "authors": [], "venue": "", "year": None,
    "doi": "", "url": "", "zotero": {"item": "", "pdf": ""}, "pdf": "source.pdf" if pdf else "",
    "pages": 0, "pagesSkipped": {}, "tags": [],
    "card": {k: "" for k in ["一句话", "问题与动机", "方法", "实验与数据", "结果", "局限", "与我的关系"]},
}
with open(os.path.join(data, "paper.json"), "w", encoding="utf-8") as f:
    json.dump(skel, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"已创建 {data}" + ("（原文已复制为 source.pdf）" if pdf else ""))
