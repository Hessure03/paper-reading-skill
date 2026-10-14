# paper-reading · 论文精读报告 skill

给 Claude Code / Codex 用的 agent skill：把**一篇论文**（本地 PDF、PDF 链接 / arXiv，或 Zotero 条目）做成一份**中文精读报告**。报告是一个单文件网页，你可以在上面高亮、批注、记笔记，笔记自动存成文件，之后 AI 可以按你的疑问答疑。

支持 **macOS / Linux / Windows**。**不需要 Zotero**。

## 报告里有什么
- 逐节讲解：先用大白话讲直观图景，再讲术语、公式和步骤
- 关键原文摘录，带页码；点页码就打开原文 PDF 的对应页
- 原文插图截图、重新排版的表格、几个可以动手玩的交互演示
- 助手的批判分析（和论文原话严格分开）、原文问题校核、自测题、结构化总结卡片
- 高亮（重点 / 懂了 / 疑问 / 概念）、批注、小节笔记、读懂进度、笔记汇总和疑问清单

## 安装

### 方式一：让 AI 帮你装（推荐）
在 Claude Code 或 Codex 里发这句话：

```text
请按 https://github.com/Hessure03/paper-reading-skill 仓库里的 INSTALL.md 安装 paper-reading skill。
```

AI 会先告诉你要装什么、装在哪、有什么风险，让你选择数据目录和是否开机自启，你同意后才会动手。

### 方式二：手动安装
1. 准备 **Python ≥ 3.9** 和 **Node.js ≥ 18**。
2. 把本仓库放到 skill 目录（文件夹名 `paper-reading`）：

| Agent | skill 目录 |
|---|---|
| Claude Code | `~/.claude/skills/paper-reading` |
| Codex | `~/.agents/skills/paper-reading` |

```bash
git clone --depth 1 https://github.com/Hessure03/paper-reading-skill.git ~/.claude/skills/paper-reading
```

没有 git 的话，下载 [ZIP](https://github.com/Hessure03/paper-reading-skill/archive/refs/heads/main.zip)，解压后放到上面的位置。Windows 上 `~` 指 `%USERPROFILE%`。

3. 安装引擎。`--root` 是报告、原文和笔记存放的位置；`--autostart yes` 表示登录时自动启动本地精读主页：

```bash
python3 ~/.claude/skills/paper-reading/engine/install.py --root ~/Papers --autostart yes
```

Windows 上用 `py -3` 或 `python` 代替 `python3`。只想先检查环境，不改任何东西，就加 `--check`。

4. 重启 agent，然后对它说：**精读这篇论文 /path/to/paper.pdf**

## 会装在哪里

| 内容 | 位置 |
|---|---|
| skill 本身（说明和引擎源码，约 250 KB） | 上面表格里的 skill 目录 |
| 引擎、Python 虚拟环境（PyMuPDF、Pillow）、KaTeX | `<数据根目录>/_paper-reading/engine/`（约 60–100 MB） |
| 论文原文、讲解源文件、你的笔记 | `<数据根目录>/_paper-reading/data/` |
| 报告（每篇一个 .html） | `<数据根目录>/reports/` |
| 设置（根目录、端口、读者背景） | `~/.config/paper-reading/config.json` |
| 登录自启（可选） | macOS LaunchAgent · Linux systemd 用户服务 · Windows 启动文件夹 |

## 使用前须知
- **本地后台服务**：精读主页运行在 `http://127.0.0.1:8614/`，只对本机开放，用来把笔记存成文件。它会把数据根目录下的文件提供给本机程序读取，所以不要把数据根目录设在存放密码或密钥的文件夹。
- **开销大**：AI 会逐页阅读全文（文字和图片都看），一篇论文要花较长时间和较多 token。
- **报告用于个人学习**：报告里有原文摘录和截图，请不要公开发布。
- **对系统的改动**：只写入上面表格里的位置。Python 依赖装在独立的虚拟环境里，不改动系统 Python。
- **报告按读者定制**：第一次使用时 AI 会问你的背景和研究方向，之后的讲解深度和"与我的关系"一节都会按这些信息来写。

## 更新与卸载

更新：

```bash
git -C ~/.claude/skills/paper-reading pull
```

拉取后再运行一次 `install.py`，不需要加参数。

停止服务并取消自启（报告、原文和笔记都保留）：

```bash
python3 <数据根目录>/_paper-reading/engine/uninstall.py
```

加上 `--remove-engine` 会连引擎和设置一起删除。最后删掉 skill 文件夹即可。任何脚本都不会删除你的报告、原文和笔记。

## 目录结构
```
SKILL.md            agent 读的主说明
INSTALL.md          给 AI 看的安装步骤（先告知、再询问、后安装）
references/         工作流程、源文件格式、写作标准、交互演示、服务说明
engine/             引擎源码（install.py 把它复制到数据根目录下）
examples/           一份完整的示例报告源文件（不含原文截图）
```

## 许可
MIT。安装时会另外下载 [KaTeX](https://katex.org/)（MIT）、[PyMuPDF](https://pymupdf.readthedocs.io/)（AGPL-3.0）和 [Pillow](https://python-pillow.org/)（MIT-CMU），它们各自遵循自己的许可证。
