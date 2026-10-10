#!/usr/bin/env python3
"""「价格错觉对比器」—— 本项目的交互入口。

为什么需要它（而不只是那份榜单报告）
------------------------------------
榜单是**通用答案**：所有人看到的是同一张表，看完就走。
对比器是**属于他的答案**：访客自己选两款，得到针对这次选择的结论。

Star 的本质是价值认可，而个性化输出的价值感远高于通用输出 ——
访客亲手试出来的「卧槽」，才会变成仓库页上的那一次点击。

设计约束（决定了技术选型）
--------------------------
1. **零 Token**：浏览器不能直连 MCP（CORS + 密钥会暴露在前端）。
   故数据随页面内嵌，来自 `--replay` 的真实快照，与报告同源。
2. **零外部依赖**：自包含单文件，可直接丢到 GitHub Pages / 任意静态托管。
3. **零装饰**：不加动画。信息密度优先，和榜单报告同一套视觉语言。
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone, timedelta

import icons

CST = timezone(timedelta(hours=8))
REPO_URL = "https://github.com/york0307/mcd-protein-value"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
background:#FAFAF8;color:#292726;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto;padding:0 20px 56px}
header{background:#DA291C;color:#fff;padding:36px 0 30px;margin-bottom:28px}
header .wrap{padding-bottom:0}
h1{font-size:27px;font-weight:600;letter-spacing:-.4px;margin-bottom:8px}
.sub{font-size:14.5px;opacity:.93}
.meta{font-size:12.5px;opacity:.8;margin-top:14px;display:flex;flex-wrap:wrap;gap:14px}
header a{color:#fff;text-decoration:underline;text-underline-offset:2px}
.pick{background:#fff;border:1px solid #E8E6E1;border-radius:12px;padding:18px 20px;margin-bottom:18px}
.row{display:grid;grid-template-columns:1fr 44px 1fr;gap:12px;align-items:end}
.sel label{display:block;font-size:12.5px;color:#6E6C68;margin-bottom:6px}
select{width:100%;font-size:14px;font-family:inherit;padding:10px 12px;border:1px solid #D9D7D1;
border-radius:8px;background:#fff;color:#292726}
select:focus{outline:2px solid #FFC72C;outline-offset:-1px}
.swap{height:40px;border:1px solid #D9D7D1;background:#F5F3EF;border-radius:8px;cursor:pointer;
font-size:15px;color:#55534F;font-family:inherit}
.swap:hover{background:#EAE8E2}
.quick{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.qb{background:#fff;border:1px solid #E8E6E1;border-radius:8px;padding:7px 13px;font-size:13px;
cursor:pointer;color:#55534F;font-family:inherit}
.qb:hover{background:#F5F3EF}
.legend{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px;padding-top:14px;
border-top:1px dashed #EDEBE6}
.lg{display:inline-flex;align-items:center;gap:5px;font-size:12px;color:#6E6C68;
background:#F7F5F1;border-radius:20px;padding:3px 9px 3px 5px}
.lg b{font-weight:600;color:#292726;font-variant-numeric:tabular-nums}
.ic{width:17px;height:17px;flex:none;display:inline-block;vertical-align:-3px}
.lg .ic{width:15px;height:15px;vertical-align:0}
.verdict{background:#292726;color:#fff;border-radius:12px;padding:20px 22px;margin-bottom:18px}
.verdict .lead{font-size:17px;font-weight:600;letter-spacing:-.2px;line-height:1.5}
.verdict .why{font-size:13.5px;opacity:.82;margin-top:10px}
.verdict b{color:#FFC72C}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:8px}
.side{background:#fff;border:1px solid #E8E6E1;border-radius:12px;padding:16px 18px}
.side.hi{border-color:#FFC72C;border-width:2px}
.side .nm{font-size:15px;font-weight:600;margin-bottom:2px;display:flex;align-items:center;gap:7px}
.side .ct{font-size:11.5px;color:#8A8781;background:#F5F3EF;border-radius:5px;padding:1px 6px;
display:inline-block;margin-bottom:12px}
.kv{display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;
border-top:1px dashed #F0EEE9}
.kv span:first-child{color:#6E6C68}
.kv span:last-child{font-variant-numeric:tabular-nums;font-weight:500}
.better{color:#0F6E56}.worse{color:#C0392B}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #E8E6E1;
border-radius:12px;overflow:hidden;font-size:13.5px}
.tw{overflow-x:auto;margin-bottom:8px}
th{background:#F5F3EF;text-align:right;font-weight:600;font-size:12.5px;color:#55534F;
padding:10px 12px;white-space:nowrap;border-bottom:1px solid #E8E6E1}
th:first-child,th:nth-child(2){text-align:left}
td{padding:10px 12px;border-bottom:1px solid #F2F0EC;text-align:right;white-space:nowrap}
td:first-child,td:nth-child(2){text-align:left}
h2{font-size:19px;font-weight:600;margin:34px 0 6px;letter-spacing:-.2px}
.h2note{font-size:13px;color:#6E6C68;margin-bottom:14px}
.cta{background:#FFF8E7;border:1px solid #F0C75E;border-radius:12px;padding:20px 22px;margin-top:28px}
.cta h3{font-size:16px;font-weight:600;margin-bottom:6px}
.cta p{font-size:13.5px;color:#6B4E00;margin-bottom:14px}
.cta .btns{display:flex;gap:10px;flex-wrap:wrap}
.cta a{display:inline-block;text-decoration:none;font-size:13.5px;font-weight:500;border-radius:8px;
padding:9px 16px;border:1px solid #292726;color:#292726;background:#fff}
.cta a.pri{background:#292726;color:#fff}
footer{margin-top:28px;padding-top:18px;border-top:1px solid #E8E6E1;font-size:12.5px;color:#8A8781}
footer a{color:#6E6C68}
@media(max-width:640px){h1{font-size:22px}.row{grid-template-columns:1fr}.cmp{grid-template-columns:1fr}}
"""

JS = """
// 注意：这里的全局变量名不能叫 __DATA__ —— 它与模板占位符同名，
// 会被 str.replace 一起替换掉，导致 `window.{...}` 这种语法错误。
var D = window.MCD_DATA;
var A = document.getElementById('a'), B = document.getElementById('b');
var defA = D.preset[0], defB = D.preset[1];

function fill(sel, keep){
  D.items.forEach(function(it, i){
    var o = document.createElement('option');
    o.value = i;
    o.textContent = it.name + ' · ¥' + pr(it.price);
    sel.appendChild(o);
  });
  sel.value = keep;
}
fill(A, defA); fill(B, defB);

function n0(v){ return Math.round(v); }
function n1(v){ return (Math.round(v*10)/10).toFixed(1); }
function n2(v){ return (Math.round(v*100)/100).toFixed(2); }
// 价格统一取整显示：榜单报告用的是整数口径，对比器必须同口径，
// 否则同一款餐品在两个页面出现两个价，会被当成数据错误。
function pr(v){ return Math.round(v); }
// 金额：整数不带小数，有零头才保留一位
function money(v){ var r = Math.round(v*10)/10; return (r % 1 === 0) ? String(Math.round(r)) : r.toFixed(1); }

// 图标引用的是页面顶部注入的 SVG symbol 雪碧，不发起任何外部请求。
function icx(id){ return '<svg class="ic" aria-hidden="true"><use href="#ic-'+id+'"/></svg>'; }

function kv(label, va, vb, better){
  var ca = '', cb = '';
  if (better === 'high') { ca = (va>vb?'better':(va<vb?'worse':'')); cb = (vb>va?'better':(vb<va?'worse':'')); }
  if (better === 'low')  { ca = (va<vb?'better':(va>vb?'worse':'')); cb = (vb<va?'better':(vb>va?'worse':'')); }
  return '<div class="kv"><span>'+label+'</span><span>' +
    '<i class="'+ca+'">'+va+'</i> &nbsp;/&nbsp; <i class="'+cb+'">'+vb+'</i></span></div>';
}

function verdict(a, b){
  var dp = pr(a.price) - pr(b.price);
  var dear = dp >= 0 ? a : b, cheap = dp >= 0 ? b : a;
  var gap = Math.abs(dp);
  var dPro = dear.protein - cheap.protein;
  var dKal = dear.kcal - cheap.kcal;
  var dNa  = dear.sodium - cheap.sodium;
  var lead = '', why = '';

  if (gap < 0.5) {
    lead = '两款价格几乎一样，蛋白质却差 <b>' + n1(Math.abs(a.protein-b.protein)) + 'g</b>';
    why = '同样的钱，买到的完全不是一回事。';
  } else if (Math.abs(dPro) <= 1) {
    if (dPro < -0.5) {
      lead = '贵的那款多花 <b>¥' + money(gap) + '</b>，蛋白质反而<b>少 ' + money(Math.abs(dPro)) + 'g</b>';
    } else {
      lead = '多花 <b>¥' + money(gap) + '</b>，蛋白质几乎没差别（差 ' + money(Math.abs(dPro)) + 'g）';
    }
    why = '多花的钱买的不是蛋白质。';
    if (dKal > 0) why += '还多摄入 ' + n0(dKal) + ' 大卡。';
    if (dKal < 0) why += '热量反而少 ' + n0(Math.abs(dKal)) + ' 大卡。';
  } else {
    var per = gap / dPro;
    lead = '多花 <b>¥' + money(gap) + '</b> 多买到 <b>' + money(dPro) + 'g</b> 蛋白质';
    why = '折合每克蛋白质约 ¥' + n2(per) + '（按标价差 ÷ 蛋白差）。';
    if (dKal > 0) why += '同时多摄入 ' + n0(dKal) + ' 大卡。';
  }
  if (Math.abs(dNa) >= 300) {
    why += (dNa > 0 ? '贵的那款钠还多 ' : '贵的那款钠少 ') + n0(Math.abs(dNa)) + 'mg。';
  }
  return '<div class="lead">' + lead + '</div><div class="why">' + why + '</div>';
}

function render(){
  var a = D.items[+A.value], b = D.items[+B.value];
  document.getElementById('verdict').innerHTML = verdict(a, b);

  // 两侧显示的是同一组对比值（A / B），只有标题和高亮不同 ——
  // 若用 it 取数，B 侧会渲染成「B / B」。
  function side(it, hi){
    return '<div class="side'+(hi?' hi':'')+'">' +
      '<div class="nm">'+icx(it.ic)+'<span>'+it.name+'</span></div><div><span class="ct">'+it.category+'</span></div>' +
      kv('价格', '¥'+pr(a.price), '¥'+pr(b.price), 'low') +
      kv('蛋白质', n1(a.protein)+'g', n1(b.protein)+'g', 'high') +
      kv('热量', n0(a.kcal), n0(b.kcal), 'low') +
      kv('钠', n0(a.sodium)+'mg', n0(b.sodium)+'mg', 'low') +
      kv('每元蛋白', n2(a.protein_per_yuan)+'g', n2(b.protein_per_yuan)+'g', 'high') +
      '</div>';
  }
  document.getElementById('cmp').innerHTML =
    side(a, a.score >= b.score) + side(b, b.score >= a.score);
}

A.addEventListener('change', render);
B.addEventListener('change', render);
document.getElementById('swap').addEventListener('click', function(){
  var t = A.value; A.value = B.value; B.value = t; render();
});
document.getElementById('rnd').addEventListener('click', function(){
  var i = Math.floor(Math.random()*D.items.length);
  var j = Math.floor(Math.random()*D.items.length);
  if (i === j) j = (j+1) % D.items.length;
  A.value = i; B.value = j; render();
});
document.getElementById('wow').addEventListener('click', function(){
  A.value = defA; B.value = defB; render();
});
render();
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>麦当劳价格错觉对比器</title>
<meta name="description" content="选两款麦当劳餐品，看看贵的那款多花的钱到底买到了什么。">
<style>__CSS__</style>
</head>
<body>
__SPRITE__
<header><div class="wrap">
<h1>麦当劳价格错觉对比器</h1>
<div class="sub">选两款餐品 —— 贵的那款，你多花的钱到底买到了什么？</div>
<div class="meta">
<span>数据：__SOURCE__</span>
<span>共 __COUNT__ 款</span>
<span>生成于 __NOW__</span>
<span>开源项目 <a href="__REPO__" target="_blank" rel="noopener">york0307/mcd-protein-value</a></span>
</div>
</div></header>

<div class="wrap">
<div class="pick">
<div class="row">
<div class="sel"><label>A 款</label><select id="a"></select></div>
<button class="swap" id="swap" title="交换">⇄</button>
<div class="sel"><label>B 款</label><select id="b"></select></div>
</div>
<div class="quick">
<button class="qb" id="wow">给我看最反直觉的一对</button>
<button class="qb" id="rnd">随机来一对</button>
<a class="qb" href="report.html" style="text-decoration:none;line-height:1.9">看完整榜单报告 →</a>
</div>
__LEGEND__
</div>

<div class="verdict" id="verdict"></div>
<div class="cmp" id="cmp"></div>

<h2>总榜 · 综合最优 __TOPN__</h2>
<p class="h2note">综合蛋白密度、每元蛋白质与钠负荷加权。想看四个专项榜和全部 __COUNT__ 款，
<a href="report.html">打开完整报告</a>。</p>
<div class="tw"><table>
<thead><tr><th>#</th><th>餐品</th><th>价格</th><th>热量</th><th>蛋白质</th><th>蛋白密度</th><th>蛋白/元</th><th>钠</th></tr></thead>
<tbody>__ROWS__</tbody>
</table></div>

<div class="cta">
<h3>觉得有用，给个 Star ⭐</h3>
<p>本项目参加 2026 麦当劳程序员创意开发大赛，榜单排名由仓库的公开 Star 数决定 —— 你的一颗 Star 就是一票。</p>
<div class="btns">
<a class="pri" href="__REPO__" target="_blank" rel="noopener">⭐ Star 这个项目</a>
<a href="__REPO__#readme" target="_blank" rel="noopener">查看源码与接入方式</a>
</div>
</div>

<footer>
价格与营养来自麦当劳官方 MCP 接口，为参赛作品，<b>非麦当劳官方产品</b>。
蛋白密度 = 蛋白质(g) ÷ 能量(kcal) × 100；每元蛋白 = 蛋白质(g) ÷ 价格(元)。
数据仅供参考，不构成营养建议；餐品、价格及供应状态以麦当劳官方渠道实时结果为准。
</footer>
</div>
<script>window.MCD_DATA = __DATA__;</script>
<script>__JS__</script>
</body>
</html>
"""


def _preset(rankings: dict) -> tuple[int, int]:
    """最有冲击力的一对：蛋白相近（±1g）但价差最大。

    与报告里「同蛋白不同价」用的是同一条判据，保证两个产物说法一致。
    """
    items = rankings["all"]
    floor = rankings.get("protein_floor", 5.0)
    elig = [x for x in items if x.get("protein", 0) >= floor] or items
    best = None
    for i in range(len(elig)):
        for j in range(i + 1, len(elig)):
            a, b = elig[i], elig[j]
            if abs(a["protein"] - b["protein"]) <= 1:
                gap = abs(a["price"] - b["price"])
                if gap > 0 and (best is None or gap > best[0]):
                    best = (gap, a["name"], b["name"])
    if not best:
        return 0, min(1, len(items) - 1)
    idx = {x["name"]: k for k, x in enumerate(items)}
    return idx.get(best[1], 0), idx.get(best[2], min(1, len(items) - 1))


def _legend(rankings: dict) -> str:
    """品类图例 —— 让图标有解释，顺带交代 20 款的构成。"""
    order: dict[str, int] = {}
    for x in rankings["all"]:
        c = x.get("category") or "未分类"
        order[c] = order.get(c, 0) + 1
    chips = "".join(
        f'<span class="lg">{icons.for_category(c)}'
        f'<span>{html.escape(str(c))}</span><b>{n}</b></span>'
        for c, n in sorted(order.items(), key=lambda kv: -kv[1]))
    return f'<div class="legend">{chips}</div>'


def render_compare(rankings: dict, meta: dict) -> str:
    items = rankings["all"]
    keep = ("name", "category", "price", "kcal", "protein",
            "sodium", "protein_per_yuan", "protein_density", "score")
    slim = []
    for x in items:
        row = {k: x.get(k, 0) for k in keep}
        row["ic"] = icons.icon_id(x.get("category"))
        slim.append(row)

    ia, ib = _preset(rankings)
    payload = {"items": slim, "preset": [ia, ib]}

    rows = []
    for i, r in enumerate(rankings["red_list"], 1):
        rows.append(
            f"<tr><td>{i}</td>"
            f'<td>{icons.for_category(r.get("category"))} {html.escape(str(r["name"]))}</td>'
            f"<td>¥{r['price']:.0f}</td><td>{r['kcal']:.0f}</td><td>{r['protein']:.0f}g</td>"
            f"<td>{r['protein_density']:.1f}</td><td>{r['protein_per_yuan']:.2f}</td>"
            f"<td>{r['sodium']:.0f}mg</td></tr>")

    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")
    return (TEMPLATE
            .replace("__SPRITE__", icons.sprite())
            .replace("__LEGEND__", _legend(rankings))
            .replace("__CSS__", CSS)
            .replace("__JS__", JS)
            .replace("__DATA__", json.dumps(payload, ensure_ascii=False))
            .replace("__ROWS__", "".join(rows))
            .replace("__SOURCE__", html.escape(str(meta.get("source", ""))))
            .replace("__COUNT__", str(len(items)))
            .replace("__TOPN__", str(len(rankings["red_list"])))
            .replace("__NOW__", now)
            .replace("__REPO__", REPO_URL))


def write_compare(rankings: dict, meta: dict, path: str = "output/index.html") -> str:
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_compare(rankings, meta))
    return path
