#!/usr/bin/env node
// 构建精读报告：node build.js <论文ID 或 数据/<论文ID> 文件夹>
//   读取 数据/<ID>/paper.json 与 src/*.txt（标记格式见 references/markup.md），
//   把截图（figs/）、交互演示（demos/）、KaTeX 全部嵌进一个 .html，写到 paper.json 的 out（相对数据根目录）。
//   报告是单文件：双击、发给别人都能看；笔记由精读主页服务存到 data/<ID>/notes/。
//   出处页码链接：paper.json 有 zotero.pdf 时打开 Zotero；否则有 pdf（如 source.pdf）时打开本地 PDF 的对应页。
const fs = require('fs');
const path = require('path');
const TOOLS = __dirname;
const SYS = path.dirname(TOOLS);
const ROOT = path.dirname(SYS);
const DATA = path.join(SYS, 'data');
let SETTINGS = {};
try { SETTINGS = JSON.parse(fs.readFileSync(path.join(TOOLS, 'settings.json'), 'utf8')); } catch (e) {}
let DOC = process.argv[2] || '.';
if (!fs.existsSync(path.join(DOC, 'paper.json')) && fs.existsSync(path.join(DATA, DOC, 'paper.json'))) DOC = path.join(DATA, DOC);
DOC = path.resolve(DOC);
const cfgPath = path.join(DOC, 'paper.json');
if (!fs.existsSync(cfgPath)) { console.error('找不到 ' + cfgPath); process.exit(2); }
const vendorDir = path.join(TOOLS, 'vendor', 'katex');
if (!fs.existsSync(path.join(vendorDir, 'katex.min.js'))) { console.error('找不到 ' + vendorDir + '，请先运行 install.sh'); process.exit(2); }
const katex = require(path.join(vendorDir, 'katex.min.js'));
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const ID = path.basename(DOC);
if (cfg.id && cfg.id !== ID) { console.error(`paper.json 的 id（${cfg.id}）和文件夹名（${ID}）不一致`); process.exit(2); }
if (!cfg.out || path.isAbsolute(cfg.out) || cfg.out.split('/').includes('..') || !/\.html$/.test(cfg.out)) { console.error('paper.json 的 out 必须是相对 ' + ROOT + ' 的 .html 路径'); process.exit(2); }
const PDFKEY = (cfg.zotero && cfg.zotero.pdf) || '';
// 没有 Zotero 时用本地 PDF：报告到 data/<ID>/<pdf> 的相对路径（file:// 和精读主页下都能打开）
const LOCALPDF = !PDFKEY && cfg.pdf ? (() => {
  const abs = path.join(DOC, cfg.pdf);
  if (!fs.existsSync(abs)) { console.error('paper.json 的 pdf 指向的文件不存在：' + abs); process.exit(2); }
  return path.relative(path.dirname(path.join(ROOT, cfg.out)), abs).split(path.sep).map(encodeURIComponent).join('/');
})() : '';
const PDF_VIA = PDFKEY ? '在 Zotero 打开' : '打开';
const NPAGES = +cfg.pages || 0;

const TAGS = {
  '原': ['yuan', '原文'], '直': ['zhi', '直观'], '讲': ['jiang', '讲解'], '术': ['shu', '术语'], '式': ['shi', '公式'],
  '重': ['zhong', '重点'], '数': ['num', '关键数字'], '评': ['ping', '助手分析'], '坑': ['keng', '易错'], '勘': ['kan', '校核'], '联': ['lian', '联系'],
  '题': ['ti', '题目'], '提': ['tishi', '提示'], '答': ['da', '答案'], '解': ['jie', '解答'], '图': ['img', ''], '演': ['demo', ''],
};
const HIDEABLE = new Set(['提', '答', '解']);
const errors = [], warns = [];
let where = '';
const jsStr = s => JSON.stringify(String(s)).replace(/</g, '\\u003c');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const pdfLink = n => PDFKEY ? `zotero://open-pdf/library/items/${PDFKEY}?page=${n}` : LOCALPDF ? `${LOCALPDF}#page=${n}` : '';
const pdfAttrs = () => PDFKEY ? '' : ' target="_blank" rel="noopener"';
function tex(src, display) {
  try { return katex.renderToString(src, { displayMode: display, throwOnError: true, strict: 'ignore', trust: false, macros: Object.assign({ '\\R': '\\mathbb{R}' }, cfg.macros || {}) }); }
  catch (e) { errors.push(`${where}: ${e.message.split('\n')[0]}  ⟵  ${src.slice(0, 80)}`); return `<code class="texerr">${esc(src)}</code>`; }
}
const usedPages = new Set();
function pageChip(label) {
  const m = label.match(/\bpp?\.\s?(\d+)/);
  if (m) {
    const n = +m[1]; usedPages.add(n);
    if (NPAGES && n > NPAGES) errors.push(`${where}: 出处 ${label} 超出总页数 ${NPAGES}`);
    const href = pdfLink(n);
    if (href) return `<a class="ref" href="${href}"${pdfAttrs()} title="${PDF_VIA}原文第 ${n} 页">${esc(label)}</a>`;
  }
  return `<span class="ref">${esc(label)}</span>`;
}
const REF_RE = /\[((?:pp?\.|Fig\.|Figs\.|Table|Tab\.|Eq\.|Eqs\.|Sec\.|Alg\.|Appx?\.|§)[^\[\]]{0,40})\]/g;
function inlineText(s) {
  let t = esc(s);
  t = t.replace(/\[([^\[\]]+)\]\(([^)\s]+)\)/g, (a, txt, url) => `<a href="${url}" target="_blank" rel="noopener">${txt}</a>`);
  t = t.replace(REF_RE, (a, lab) => pageChip(lab.replace(/&amp;/g, '&')));
  return t.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>');
}
function rich(s) {
  let out = '', i = 0;
  while (i < s.length) {
    if (s.startsWith('$$', i)) { const j = s.indexOf('$$', i + 2); if (j < 0) { errors.push(`${where}: 未闭合 $$`); break; } out += `<div class="dm">${tex(s.slice(i + 2, j).trim(), true)}</div>`; i = j + 2; }
    else if (s[i] === '$') { const j = s.indexOf('$', i + 1); if (j < 0) { errors.push(`${where}: 未闭合 $`); break; } out += tex(s.slice(i + 1, j), false); i = j + 1; }
    else { let j = s.indexOf('$', i); if (j < 0) j = s.length; out += inlineText(s.slice(i, j)).replace(/\n/g, '<br>'); i = j; }
  }
  return out.replace(/<br>(<div class="dm">)/g, '$1').replace(/(<\/div>)<br>/g, '$1');
}
// 连续以 | 开头的行 = 表格（第一行表头）；连续以 "- " 开头的行 = 列表
function blockHtml(text) {
  const lines = text.split('\n'); let out = '', buf = [], tbl = [], lst = [];
  const flushBuf = () => { if (buf.length) { out += `<p>${rich(buf.join('\n'))}</p>`; buf = []; } };
  const flushTbl = () => {
    if (!tbl.length) return;
    const rows = tbl.map(l => l.replace(/^\|/, '').replace(/\|\s*$/, '').split(' | ').map(c => c.trim()));
    out += '<div class="tw"><table><thead><tr>' + rows[0].map(c => `<th>${rich(c)}</th>`).join('') + '</tr></thead><tbody>' +
      rows.slice(1).map(r => '<tr>' + r.map(c => `<td>${rich(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>';
    tbl = [];
  };
  const flushLst = () => { if (lst.length) { out += '<ul>' + lst.map(l => `<li>${rich(l)}</li>`).join('') + '</ul>'; lst = []; } };
  for (const l of lines) {
    if (/^\|/.test(l)) { flushBuf(); flushLst(); tbl.push(l); }
    else if (/^- /.test(l)) { flushBuf(); flushTbl(); lst.push(l.slice(2)); }
    else if (l.trim() === '') { flushBuf(); flushTbl(); flushLst(); }
    else { flushTbl(); flushLst(); buf.push(l); }
  }
  flushBuf(); flushTbl(); flushLst();
  return out;
}
function parsePages(spec) {
  const out = [];
  for (const part of (spec || '').replace(/pp?\./g, '').split(/[,，]/)) {
    const m = part.trim().match(/^(\d+)(?:\s*[-–]\s*(\d+))?$/); if (!m) continue;
    for (let k = +m[1]; k <= +(m[2] || m[1]); k++) out.push(k);
  }
  return out;
}
const mime = f => ({ '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml' })[path.extname(f).toLowerCase()];
let figBytes = 0;
function embedImg(rel) {
  const p = path.join(DOC, rel);
  if (!fs.existsSync(p) || !mime(p)) { errors.push(`${where}: 图片不存在或格式不支持 ${rel}`); return ''; }
  const buf = fs.readFileSync(p); figBytes += buf.length;
  if (buf.length > 450e3) warns.push(`${where}: ${rel} 有 ${(buf.length / 1024) | 0} KB，建议压缩（figcrop.sh 默认输出 WebP）`);
  return `data:${mime(p)};base64,${buf.toString('base64')}`;
}

// ---------- 解析 src/*.txt ----------
const srcDir = path.join(DOC, 'src');
const files = fs.existsSync(srcDir) ? fs.readdirSync(srcDir).filter(f => /^\d+_.*\.txt$/.test(f)).sort() : [];
if (!files.length) errors.push('src/ 里没有 NN_*.txt 内容文件');
const chapters = [], secs = [];
for (const f of files) {
  const lines = fs.readFileSync(path.join(srcDir, f), 'utf8').split('\n');
  let sec = null, blk = null;
  lines.forEach((raw, li) => {
    const line = raw.replace(/\s+$/, '');
    let m;
    if ((m = line.match(/^## (.+)$/))) { chapters.push({ title: m[1], secs: [] }); sec = null; blk = null; }
    else if ((m = line.match(/^@@ ([a-z0-9][a-z0-9-]*) \| ([^|]+?)(?: \| (.+))?$/))) {
      if (!chapters.length) chapters.push({ title: '正文', secs: [] });
      sec = { key: m[1], title: m[2].trim(), pages: parsePages(m[3]), pspec: (m[3] || '').trim(), blocks: [] };
      secs.push(sec); chapters[chapters.length - 1].secs.push(sec); blk = null;
    } else if ((m = line.match(/^(.):\s?(.*)$/)) && TAGS[m[1]]) {
      if (!sec) { errors.push(`${f}:${li + 1} 标签行出现在任何 @@ 小节之前`); return; }
      blk = { tag: m[1], text: m[2] }; sec.blocks.push(blk);
      if (m[1] === '图' || m[1] === '演') blk = null;
    } else if (line.trim() === '') { if (blk) blk.text += '\n'; }
    else if (blk) blk.text += '\n' + line;
    else if (sec) errors.push(`${f}:${li + 1} 无标签的行：${line.slice(0, 40)}`);
    else if (line.trim() && !line.startsWith('#')) errors.push(`${f}:${li + 1} 小节之外的行：${line.slice(0, 40)}`);
  });
}
const keys = new Set();
for (const s of secs) { if (keys.has(s.key)) errors.push(`小节 key 重复：${s.key}`); keys.add(s.key); }

// 结构化卡片（paper.json 的 card，字段可自定义）作为最后一节
if (cfg.card && typeof cfg.card === 'object' && Object.keys(cfg.card).length) {
  for (const [k, v] of Object.entries(cfg.card)) if (!v) warns.push(`card 的「${k}」是空的`);
  const rows = Object.entries(cfg.card).map(([k, v]) => `| **${k}** | ${String(v).replace(/\n/g, ' ')}`);
  const sec = { key: 'card', title: '结构化卡片', pages: [], pspec: '', blocks: [{ tag: '重', text: '| 项目 | 内容\n' + rows.join('\n') }] };
  if (keys.has('card')) errors.push('小节 key「card」保留给结构化卡片');
  chapters.push({ title: '汇总', secs: [sec] }); secs.push(sec);
} else warns.push('paper.json 没有 card（结构化卡片）');

// ---------- 生成 HTML ----------
let secHtml = '', nQuiz = 0;
chapters.forEach((c, ci) => c.secs.forEach(s => {
  where = '§' + s.key;
  const isQ = s.blocks.some(b => b.tag === '题');
  let body = '', bi = 0;
  for (const b of s.blocks) {
    if (b.tag === '图') {
      const [src, ...cap] = b.text.split('|'); const data = embedImg(src.trim());
      body += `<figure class="fig"><img loading="lazy" src="${data}" alt="${esc(cap.join('|').trim().replace(/\[[^\]]*\]/g, '').replace(/\*\*|\$/g, '').trim().slice(0, 80))}" data-act="zoom">${cap.length ? `<figcaption>${rich(cap.join('|').trim())}</figcaption>` : ''}</figure>\n`;
      continue;
    }
    if (b.tag === '演') {
      const p = path.join(DOC, b.text.trim());
      if (!fs.existsSync(p)) { errors.push(`${where}: 交互演示不存在 ${b.text.trim()}`); continue; }
      body += `<div class="demo" data-nohl>${fs.readFileSync(p, 'utf8')}</div>\n`;
      continue;
    }
    const [cls, label] = TAGS[b.tag];
    const hide = HIDEABLE.has(b.tag) || (isQ && b.tag === '评');
    if (hide) nQuiz++;
    let text = b.text.replace(/\n+$/, ''), lab = label, lang = '';
    if (b.tag === '原') {
      const m = text.match(/^\s*\[([^\]]+)\]\s*/);
      if (m) { lab += ' ' + m[1]; text = text.slice(m[0].length); const pm = m[1].match(/\bp\.?\s?(\d+)/); if (pm) usedPages.add(+pm[1]); }
      else warns.push(`${where}: 原文块缺少出处，写成「原: [p.3] …」`);
      lang = ' lang="en"';
    }
    const content = b.tag === '式' ? `<div class="dm">${tex(text, true)}</div>` : blockHtml(text);
    let labHtml = esc(lab);
    if (b.tag === '原') { const pm = lab.match(/\bp\.?\s?(\d+)/); if (pm && pdfLink(+pm[1])) labHtml = `<a href="${pdfLink(+pm[1])}"${pdfAttrs()} title="${PDF_VIA}原文">${esc(lab)}</a>`; }
    body += `<section class="blk b-${cls}${hide ? ' hideable' : ''}" data-b="${s.key}-${bi++}"${lang}><span class="lab">${labHtml}</span><div class="bc">${content}</div></section>\n`;
  }
  const pchip = s.pspec ? pageChip(/^p/.test(s.pspec) ? s.pspec : 'p.' + s.pspec) : '';
  secHtml += `<article class="sec" id="s-${s.key}" data-k="${s.key}" data-ch="${ci}">
<header class="sec-h"><h2>${rich(s.title)}</h2>${pchip}<button class="done-btn" data-act="done" title="标记本节已读懂">✓ 读懂了</button></header>
<div class="xp">${body}</div>
<div class="note-slot"></div>
</article>\n`;
}));
where = 'toc';
let toc = '';
for (const c of chapters) {
  if (!c.secs.length) continue;
  toc += `<details class="toc-ch" open><summary>${esc(c.title)}</summary><ol>`;
  for (const s of c.secs) toc += `<li><a href="#s-${s.key}" data-toc="${s.key}"><span class="tt">${rich(s.title).replace(/<a [^>]*>|<\/a>/g, '')}</span><i class="dots"></i></a></li>`;
  toc += '</ol></details>';
}

// 页码覆盖：每一页都必须被某个小节声明（@@ … | p.N）或在 pagesSkipped 里说明原因
const covered = new Set(); secs.forEach(s => s.pages.forEach(p => covered.add(p)));
const skipped = cfg.pagesSkipped || {};
const uncovered = [];
if (NPAGES) { for (let k = 1; k <= NPAGES; k++) if (!covered.has(k) && !skipped[k]) uncovered.push(k); }
else warns.push('paper.json 没有 pages（PDF 总页数），无法检查是否每页都读过');
if (uncovered.length) errors.push(`以下页没有被任何小节覆盖：${uncovered.join(', ')}（在 @@ 行写 | p.N，或在 pagesSkipped 里写原因）`);

// ---------- 信息头 ----------
const a = cfg.authors || [];
const authors = a.length > 6 ? a.slice(0, 6).join(', ') + ' 等' : a.join(', ');
const links = [];
if (cfg.doi) links.push(`<a href="https://doi.org/${esc(cfg.doi)}" target="_blank" rel="noopener">DOI ${esc(cfg.doi)}</a>`);
if (cfg.zotero && cfg.zotero.item) links.push(`<a href="zotero://select/library/items/${esc(cfg.zotero.item)}">在 Zotero 中定位</a>`);
if (PDFKEY || LOCALPDF) links.push(`<a href="${pdfLink(1)}"${pdfAttrs()}>打开原文 PDF</a>`);
if (cfg.url) links.push(`<a href="${esc(cfg.url)}" target="_blank" rel="noopener">论文主页</a>`);
const venueText = cfg.venue && cfg.year && String(cfg.venue).includes(String(cfg.year)) ? cfg.venue : [cfg.venue, cfg.year].filter(Boolean).join(' · ');
const header = `<div class="meta-row"><span class="venue">${esc(venueText)}</span>${(cfg.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>
<h1 lang="en">${esc(cfg.title || ID)}</h1>${cfg.titleZh ? `<div class="zh">${esc(cfg.titleZh)}</div>` : ''}
<div class="authors" lang="en">${esc(authors)}</div><div class="links">${links.join('<span>·</span>')}</div>`;

// ---------- KaTeX 内嵌（字体只保留 woff2） ----------
let kcss = fs.readFileSync(path.join(vendorDir, 'katex.min.css'), 'utf8');
kcss = kcss.replace(/src:url\(fonts\/([^)]+?\.woff2)\) format\("woff2"\)(?:,url\([^)]*\) format\("[^"]*"\))*/g, (all, f) =>
  `src:url(data:font/woff2;base64,${fs.readFileSync(path.join(vendorDir, 'fonts', f)).toString('base64')}) format("woff2")`);
const kjs = fs.readFileSync(path.join(vendorDir, 'katex.min.js'), 'utf8');
const cjs = fs.readFileSync(path.join(vendorDir, 'contrib', 'copy-tex.min.js'), 'utf8');

const build = new Date(Date.now() - new Date().getTimezoneOffset() * 6e4).toISOString().slice(0, 16).replace('T', ' ');
const fill = {
  TITLE: esc(cfg.short ? cfg.short + ' · 精读' : (cfg.title || ID)), SHORT: esc(cfg.short || ID), HEADER: header, TOC: toc, SECTIONS: secHtml,
  NSEC: String(secs.length), STORE_KEY: esc(ID), OUT_REL: esc(cfg.out), PORT: String(SETTINGS.port || 8614),
  NOTES_DIR_JSON: jsStr(`<数据根目录>/_paper-reading/data/${ID}/notes/`),
  PDFKEY: esc(PDFKEY), QUIZ: nQuiz ? '1' : '0', BUILD: build, KATEX_CSS: kcss, KATEX_JS: kjs, COPYTEX_JS: cjs,
};
const tpl = fs.readFileSync(path.join(TOOLS, 'template.html'), 'utf8');
const outAbs = path.join(ROOT, cfg.out);
fs.mkdirSync(path.dirname(outAbs), { recursive: true });
const html = tpl.replace(/\{\{([A-Z_]+)\}\}/g, (all, k) => (k in fill ? fill[k] : all));
fs.writeFileSync(outAbs, html);
cfg.sections = secs.length; cfg.built = build;
fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\n');

console.log(`已构建 ${secs.length} 节、图片 ${(figBytes / 1024) | 0} KB、报告 ${(Buffer.byteLength(html) / 1024) | 0} KB → ${outAbs}`);
if (NPAGES) console.log(`页码覆盖：${NPAGES - uncovered.length}/${NPAGES}${Object.keys(skipped).length ? '（跳过：' + Object.entries(skipped).map(([k, v]) => k + ' ' + v).join('；') + '）' : ''}`);
if (warns.length) { console.log('提醒：'); warns.forEach(e => console.log('  ' + e)); }
if (errors.length) { console.log('问题：'); errors.forEach(e => console.log('  ' + e)); process.exitCode = 1; }
