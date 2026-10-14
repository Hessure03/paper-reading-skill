# Interactive demos and figures

## When to make a demo
2–5 per paper, only where "trying it" beats reading: how raw sensor data becomes the network input; how an action/parameter maps to motion; how reward terms combine; where modalities are fused; a result table you can slice (per object, per split). Every parameter must come from the paper (cite it in the demo title badge); anything assumed or simplified is labelled "示意".

## Fragment format (`data/<ID>/demos/<name>.html`)
The build inlines the file into `<div class="demo" data-nohl>` (highlighting is disabled inside). Structure:
```html
<h4>交互：一句话说明<span class="badge">参数来自 Table I；图形为示意</span></h4>
<canvas id="xxCv" height="250" aria-label="…"></canvas>
<div class="ctrl">
  <label>参数名 <output id="xxAO"></output><input type="range" id="xxA" min="0" max="100" value="50"></label>
  <button type="button" id="xxBtn">开关</button>
</div>
<pre class="out" id="xxOut"></pre>
<div class="note">怎么玩、看什么。</div>
<script>
(function(){
  const {$, $$, css, hexA, fit, arrow, onRedraw} = R;
  const c = $('#xxCv');
  function draw(){
    const {x, w, h} = fit(c);           // clears and sizes the canvas; never read c.height yourself
    x.fillStyle = css('--s1');           // theme colours only
    …
    $('#xxOut').textContent = '…';
  }
  $('#xxA').addEventListener('input', draw);
  onRedraw(draw);                        // redraws on resize, theme switch, search filter
})();
</script>
```
- **Prefix every id** with a short demo-specific prefix (several demos share one page).
- Helpers on `window.R`: `$`, `$$`, `css(var)`, `hexA(hex, alpha)`, `fit(canvas) → {x, w, h}`, `arrow(ctx, x1, y1, x2, y2, colour, headSize)`, `onRedraw(fn)`, `redraw()`.
- Colours: `--ink --ink2 --line --bg --paper --accent`, series `--s1` blue `--s2` orange `--s3` green `--s4` red `--s5` purple `--s6` grey. They switch with light/dark theme.
- Layout helpers: `.row2` (two columns, one on phones), `.ctrl` (controls row), `button.on` (toggled state), `pre.out` (readout), `.note`.
- Use pointer events (`pointerdown/move/up`) for dragging so it works on touch; keep canvases ≤ 300 px tall.
- Test each demo in the browser: moves, toggles, both themes, 375 px width.

## Figures
- Crop with `pdftool.py crop` (WebP). Caption format: `**Fig.N** 中文说明（不是逐字翻译，说明这张图要看什么）。[p.N]`.
- Put the figure right where the text discusses it, not in a gallery.
- Plots: when you read values off a plot, say they are estimates.
