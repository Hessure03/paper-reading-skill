#!/usr/bin/env python3
"""PDF 工具（替代 poppler / cwebp，macOS、Linux、Windows 通用）。用引擎 venv 里的 Python 运行：
  python pdftool.py info   <PDF>                          页数、页面尺寸、有没有文字层
  python pdftool.py render <PDF> <输出目录> [dpi]          每页渲染成 p-NN.jpg 给助手看（默认 110 dpi）
  python pdftool.py text   <PDF> <页> [末页] [--layout]    逐页提取文字（--layout 按版面排序，适合表格）
  python pdftool.py find   <PDF> <页> [关键词…]           列出文字块坐标（pt，原点左上角），默认标出图注 / 表注
  python pdftool.py crop   <PDF> <页> <x> <y> <宽> <高> <输出.webp> [dpi]
                                                         截取区域存为 WebP；整页写 0 0 0 0；dpi 默认 200
坐标单位都是 PDF 的 pt（= 72 dpi 渲染图的像素）。依赖：PyMuPDF、Pillow（install.py 已装进 venv）。
"""
import io
import os
import re
import sys

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("缺少 PyMuPDF：请用引擎 venv 里的 Python 运行本脚本（路径见 ~/.config/paper-reading/config.json 的 python），或重新运行 install.py")


def open_pdf(p):
    if not os.path.isfile(p):
        sys.exit(f"找不到 PDF：{p}")
    return fitz.open(p)


def has_text(doc):
    return any(doc[i].get_text().strip() for i in range(min(2, doc.page_count)))


def cmd_info(a):
    doc = open_pdf(a[0])
    r = doc[0].rect
    print(f"总页数：{doc.page_count}；页面尺寸：{r.width:.0f} x {r.height:.0f} pt")
    print("PDF 有文字层：用 text 子命令逐页提取文字" if has_text(doc) else "PDF 没有文字层（扫描版）：只能看图阅读")


def cmd_render(a):
    doc = open_pdf(a[0])
    out = a[1]
    dpi = int(a[2]) if len(a) > 2 else 110
    os.makedirs(out, exist_ok=True)
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=dpi).save(os.path.join(out, f"p-{i:02d}.jpg"), jpg_quality=75)
    cmd_info(a[:1])
    print(f"阅读图：{doc.page_count} 张（{dpi} dpi）→ {out}")


def cmd_text(a):
    layout = "--layout" in a
    a = [x for x in a if x != "--layout"]
    doc = open_pdf(a[0])
    first = int(a[1])
    last = int(a[2]) if len(a) > 2 else first
    for n in range(first, last + 1):
        if not 1 <= n <= doc.page_count:
            sys.exit(f"页码 {n} 超出范围 1–{doc.page_count}")
        if last > first:
            print(f"===== 第 {n} 页 =====")
        print(doc[n - 1].get_text("text", sort=layout))


def cmd_find(a):
    doc = open_pdf(a[0])
    n = int(a[1])
    keys = [k.lower() for k in a[2:]]
    page = doc[n - 1]
    print(f"第 {n} 页：宽 {page.rect.width:.0f} pt × 高 {page.rect.height:.0f} pt")
    cap = re.compile(r"^(fig\.?|figure|table|tab\.)\s*[0-9ivx]+", re.I)
    for x0, y0, x1, y1, text, *_ in page.get_text("blocks", sort=True):
        text = " ".join(text.split())
        if not text or (keys and not any(k in text.lower() for k in keys)):
            continue
        mark = "◆图注/表注" if cap.match(text) else "  "
        print(f"{mark} x={x0:6.1f}–{x1:6.1f}  y={y0:6.1f}–{y1:6.1f}  {text[:90]}")


def cmd_crop(a):
    from PIL import Image
    doc = open_pdf(a[0])
    n = int(a[1])
    x, y, w, h = (float(v) for v in a[2:6])
    out = a[6]
    dpi = int(a[7]) if len(a) > 7 else 200
    page = doc[n - 1]
    clip = None if w == 0 else fitz.Rect(x, y, x + w, y + h)
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "WEBP", quality=82, method=6)
    print(f"→ {out}  {os.path.getsize(out) // 1024} KB  ({img.width}×{img.height}px)")


CMDS = {"info": (cmd_info, 1), "render": (cmd_render, 2), "text": (cmd_text, 2), "find": (cmd_find, 2), "crop": (cmd_crop, 7)}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS or len(sys.argv) - 2 < CMDS[sys.argv[1]][1]:
        sys.exit(__doc__)
    fn, _ = CMDS[sys.argv[1]]
    fn(sys.argv[2:])
