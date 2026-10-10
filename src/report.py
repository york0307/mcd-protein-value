#!/usr/bin/env python3
"""静态榜单报告生成器 —— 本项目的「传播产物」。

设计前提：**看报告的人不需要有 MCP Token**。
因此报告是自包含单文件 HTML（无外部依赖），可直接托管到 GitHub Pages 或截图分享。
"""

from __future__ import annotations

import html
from datetime import datetime, timezone, timedelta

import icons
from numfmt import fmt

CST = timezone(timedelta(hours=8))

# 报告的转化入口：看报告的人 → 仓库 → Star。
# 榜单是「传播产物」，仓库是「转化终点」，两者必须互相可见。
REPO_URL = "https://github.com/york0307/mcd-protein-value"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
background:#FAFAF8;color:#292726;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 64px}
header{background:#DA291C;color:#fff;padding:44px 0 38px;margin-bottom:32px}
header .wrap{padding-bottom:0}
h1{font-size:30px;font-weight:600;letter-spacing:-.4px;margin-bottom:10px}
.sub{font-size:15px;opacity:.92;font-weight:400}
.meta{font-size:12.5px;opacity:.78;margin-top:16px;display:flex;flex-wrap:wrap;gap:16px}
.notice{background:#FFF4CE;border:1px solid #F0C75E;border-radius:10px;padding:12px 16px;
font-size:13px;color:#6B4E00;margin-bottom:28px}
h2{font-size:19px;font-weight:600;margin:40px 0 6px;letter-spacing:-.2px}
.h2note{font-size:13px;color:#6E6C68;margin-bottom:16px}
.grid{display:grid;gap:12px}
.g4{grid-template-columns:repeat(auto-fit,minmax(232px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.card{background:#fff;border:1px solid #E8E6E1;border-radius:12px;padding:16px 18px}
.card .lab{font-size:12.5px;color:#6E6C68;margin-bottom:6px}
.card .val{font-size:26px;font-weight:600;letter-spacing:-.5px;line-height:1.2}
.card .val small{font-size:13px;font-weight:400;color:#6E6C68;margin-left:3px}
.card .who{font-size:12.5px;color:#8A8781;margin-top:8px;padding-top:8px;border-top:1px dashed #E8E6E1}
.ins{background:#fff;border:1px solid #E8E6E1;border-left:3px solid #FFC72C;border-radius:10px;
padding:14px 18px;margin-bottom:10px;font-size:14px}
.ins b{font-weight:600}
.ins .tag{display:inline-block;font-size:11.5px;background:#FFF1D6;color:#8A5A00;
border-radius:5px;padding:1px 7px;margin-right:8px;vertical-align:1px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #E8E6E1;
border-radius:12px;overflow:hidden;font-size:13.5px}
.tw{overflow-x:auto;margin-bottom:8px}
th{background:#F5F3EF;text-align:right;font-weight:600;font-size:12.5px;color:#55534F;
padding:11px 12px;white-space:nowrap;border-bottom:1px solid #E8E6E1}
th:first-child,th:nth-child(2),th:nth-child(3){text-align:left}
td{padding:11px 12px;border-bottom:1px solid #F2F0EC;text-align:right;white-space:nowrap}
td:first-child,td:nth-child(2),td:nth-child(3){text-align:left}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:#FDFCF9}
.rk{display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;
border-radius:6px;background:#F0EEE9;color:#6E6C68;font-size:12px;font-weight:600}
.rk1{background:#FFC72C;color:#292726}.rk2{background:#D9D7D1;color:#292726}.rk3{background:#E8B27E;color:#292726}
.pn{display:inline-flex;align-items:center;gap:6px;font-weight:500}
.mm{font-size:11px;font-weight:400;color:#8A5A00;background:#FFF1D6;border-radius:4px;
padding:0 5px;margin-left:6px;cursor:help}
.ic{width:17px;height:17px;flex:none;display:inline-block;vertical-align:-3px}
.card .lab .ic{width:16px;height:16px;vertical-align:-2px;margin-right:2px}
.cat{font-size:11.5px;color:#8A8781;background:#F5F3EF;border-radius:5px;padding:1px 6px}
.bar{position:relative;min-width:64px}
.bar i{position:absolute;left:0;top:50%;transform:translateY(-50%);height:16px;
background:#FFC72C;border-radius:3px;opacity:.55}
.bar span{position:relative;padding-left:2px;font-variant-numeric:tabular-nums}
.good{color:#0F6E56;font-weight:500}.bad{color:#C0392B;font-weight:500}
.warn{color:#B26A00;font-weight:500}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.tab{background:#fff;border:1px solid #E8E6E1;border-radius:8px;padding:7px 14px;font-size:13px;
cursor:pointer;color:#55534F;font-family:inherit}
.tab.on{background:#292726;border-color:#292726;color:#fff}
.pane{display:none}.pane.on{display:block}
.method{background:#fff;border:1px solid #E8E6E1;border-radius:12px;padding:18px 20px;font-size:13.5px}
.method h3{font-size:14px;font-weight:600;margin:14px 0 6px}
.method h3:first-child{margin-top:0}
.method code{background:#F5F3EF;border-radius:4px;padding:1.5px 6px;font-size:12.5px;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.method ul{margin:6px 0 0 20px}
.method li{margin-bottom:5px}
footer{margin-top:40px;padding-top:20px;border-top:1px solid #E8E6E1;font-size:12.5px;color:#8A8781}
footer a{color:#6E6C68}
header a{color:#fff;text-decoration:underline;text-underline-offset:2px}
.cta{background:#FFF8E7;border:1px solid #F0C75E;border-radius:12px;padding:20px 22px}
.cta h3{font-size:16px;font-weight:600;margin-bottom:6px;color:#292726}
.cta p{font-size:13.5px;color:#6B4E00;margin-bottom:14px}
.cta .btns{display:flex;gap:10px;flex-wrap:wrap}
.cta a{display:inline-block;text-decoration:none;font-size:13.5px;font-weight:500;
border-radius:8px;padding:9px 16px;border:1px solid #292726;color:#292726;background:#fff}
.cta a:hover{background:#F5F3EF}
.cta a.pri{background:#292726;color:#fff}
.cta a.pri:hover{background:#000}
.cta .tip{font-size:12.5px;color:#8A6A00;margin-top:14px;padding-top:12px;border-top:1px dashed #E8C87A}
.cta .tip code{background:#FFF1D6;border-radius:4px;padding:1.5px 6px;font-size:12px;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
@media(max-width:640px){h1{font-size:23px}.card .val{font-size:22px}}
@media print{header{background:#DA291C!important;-webkit-print-color-adjust:exact}
.tab{display:none}.pane{display:block!important;page-break-inside:avoid}}
"""

JS = """
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click',function(){
    var g=t.closest('.tabs').dataset.group;
    document.querySelectorAll('.tab[data-group="'+g+'"]').forEach(function(x){x.classList.remove('on')});
    document.querySelectorAll('.pane[data-group="'+g+'"]').forEach(function(x){x.classList.remove('on')});
    t.classList.add('on');
    var p=document.getElementById(t.dataset.target);
    if(p)p.classList.add('on');
  });
});
"""


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def bar(value: float, maximum: float, text: str) -> str:
    pct = 0 if maximum <= 0 else max(4, min(100, value / maximum * 100))
    return f'<div class="bar"><i style="width:{pct:.0f}%"></i><span>{esc(text)}</span></div>'


def _rank_badge(i: int) -> str:
    cls = {1: "rk rk1", 2: "rk rk2", 3: "rk rk3"}.get(i, "rk")
    return f'<span class="{cls}">{i}</span>'


def _metric_cards(rankings: dict) -> str:
    best_v = rankings["by_protein_value"][0]
    best_d = rankings["by_protein_density"][0]
    best_k = rankings["by_kcal_value"][0]
    worst_s = rankings["by_sodium"][0]
    cards = [
        ("蛋白质性价比之王", fmt(best_v["protein_per_yuan"], 2), "g / 元",
         f'{esc(best_v["name"])} · ¥{fmt(best_v["price"], 0)} · 蛋白 {fmt(best_v["protein"], 0)}g'),
        ("蛋白密度之王", fmt(best_d["protein_density"], 1), "g / 100kcal",
         f'{esc(best_d["name"])} · 每 100 大卡给 {fmt(best_d["protein_density"], 1)}g 蛋白'),
        ("热量性价比之王", fmt(best_k["kcal_per_yuan"], 0), "kcal / 元",
         f'{esc(best_k["name"])} · ¥{fmt(best_k["price"], 0)} 换 {fmt(best_k["kcal"], 0)} 大卡'),
        ("钠含量警戒", fmt(worst_s["sodium"], 0), "mg",
         f'{esc(worst_s["name"])} · 占每日上限 {fmt(worst_s["sodium_pct"] * 100, 0)}%'),
    ]
    return "".join(
        f'<div class="card"><div class="lab">{esc(lab)}</div>'
        f'<div class="val">{esc(v)}<small>{esc(unit)}</small></div>'
        f'<div class="who">{esc(who)}</div></div>'
        for lab, v, unit, who in cards
    )


def _insights(rankings: dict) -> str:
    allx = rankings["all"]
    out = []
    if len(allx) >= 2:
        best, worst = allx[0], allx[-1]

        # 同蛋白不同价：找蛋白质相近（±1g）但价差最大的一对。
        # 这比单纯比「最高 vs 最低每元蛋白」更有说服力 —— 后者常被 0 蛋白饮品
        # （分母陷阱）或拿咖啡凑数，结论失真。
        floor = rankings.get("protein_floor", 5.0)
        elig = [x for x in allx if x.get("protein", 0) >= floor]
        pair = None
        for i in range(len(elig)):
            for j in range(i + 1, len(elig)):
                a, b = elig[i], elig[j]
                if abs(a["protein"] - b["protein"]) <= 1:
                    gap = abs(a["price"] - b["price"])
                    if gap > 0 and (pair is None or gap > pair[0]):
                        cheap, dear = (a, b) if a["price"] < b["price"] else (b, a)
                        pair = (gap, cheap, dear)
        if pair:
            gap, cheap, dear = pair
            dk = dear["kcal"] - cheap["kcal"]
            extra = f'，还多摄入 {fmt(dk, 0)} 大卡' if dk > 0 else ""
            out.append(("同蛋白不同价",
                        f'<b>{esc(cheap["name"])}</b>（¥{fmt(cheap["price"], 0)}）与 '
                        f'<b>{esc(dear["name"])}</b>（¥{fmt(dear["price"], 0)}）蛋白质都是 '
                        f'{fmt(cheap["protein"], 0)}g 左右，价差却达 <b>¥{fmt(gap, 0)}</b>'
                        f'{extra} —— 多花的钱买的不是蛋白质。'))

        hi_na = max(allx, key=lambda x: x["sodium"])
        out.append(("钠陷阱",
                    f'<b>{esc(hi_na["name"])}</b> 单品含钠 {fmt(hi_na["sodium"], 0)}mg，'
                    f'相当于一天建议上限（2000mg）的 <b>{fmt(hi_na["sodium_pct"] * 100, 0)}%</b>。'))
        out.append(("综合最优",
                    f'综合蛋白密度、性价比与钠负荷后，<b>{esc(best["name"])}</b> 以 '
                    f'{fmt(best["score"], 1)} 分排名第一；垫底的是 '
                    f'<b>{esc(worst["name"])}</b>（{fmt(worst["score"], 1)} 分）。'))
    cats = rankings["best_in_category"]
    if cats:
        top = cats[0]
        out.append(("品类速查",
                    f'<b>{esc(top["category"])}</b> 里最优是 <b>{esc(top["best"]["name"])}</b>'
                    f'（{fmt(top["best"]["score"], 1)} 分）。'))
    return "".join(
        f'<div class="ins"><span class="tag">{esc(tag)}</span>{body}</div>'
        for tag, body in out
    )


_MATCH_TIP = ("规格推定：营养库与菜单名称不完全一致，"
              "已去掉规格修饰后匹配，价格对应菜单同名单品")


def _match_mark(r: dict) -> str:
    """非精确匹配的餐品必须标出来 —— 榜单可以少收录，但不能悄悄错配。"""
    if r.get("match") == "exact" or not r.get("match"):
        return ""
    return f'<span class="mm" title="{_MATCH_TIP}">规格推定</span>'


def _table(rows: list[dict], score_max: float, show_score: bool = True) -> str:
    head = ("<tr><th>#</th><th>餐品</th><th>分类</th><th>价格</th><th>热量</th>"
            "<th>蛋白质</th><th>蛋白密度</th><th>蛋白/元</th><th>钠</th>"
            + ("<th>综合分</th>" if show_score else "") + "</tr>")
    body = []
    for i, r in enumerate(rows, 1):
        dcls = "good" if r["protein_density"] >= 6 else ("" if r["protein_density"] >= 3 else "warn")
        ncls = "bad" if r["sodium"] >= 800 else ("warn" if r["sodium"] >= 500 else "")
        body.append(
            "<tr>"
            f"<td>{_rank_badge(i)}</td>"
            f'<td><span class="pn">{icons.for_category(r.get("category"))}'
            f'{esc(r["name"])}{_match_mark(r)}</span></td>'
            f'<td><span class="cat">{esc(r["category"])}</span></td>'
            f'<td>¥{fmt(r["price"], 0)}</td>'
            f'<td>{fmt(r["kcal"], 0)}</td>'
            f'<td>{fmt(r["protein"], 0)}g</td>'
            f'<td class="{dcls}">{fmt(r["protein_density"], 1)}</td>'
            f'<td>{fmt(r["protein_per_yuan"], 2)}</td>'
            f'<td class="{ncls}">{fmt(r["sodium"], 0)}mg</td>'
            + (f'<td>{bar(r["score"], score_max, fmt(r["score"], 1))}</td>' if show_score else "")
            + "</tr>"
        )
    return f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


def _panes(rankings: dict, score_max: float) -> str:
    floor = rankings.get("protein_floor", 5.0)
    specs = [
        ("pvalue", "蛋白质性价比", f"每元能买到多少克蛋白质（仅统计蛋白 ≥ {floor:.0f}g 的餐品）",
         rankings["by_protein_value"]),
        ("pdensity", "蛋白密度", f"每 100 大卡含多少克蛋白质（仅统计蛋白 ≥ {floor:.0f}g 的餐品）",
         rankings["by_protein_density"]),
        ("kvalue", "热量性价比", "每元能买到多少大卡", rankings["by_kcal_value"]),
        ("sodium", "钠警戒", "单品含钠越高越靠前", rankings["by_sodium"]),
    ]
    tabs = "".join(
        f'<button class="tab{" on" if i == 0 else ""}" data-group="g1" data-target="p-{key}">{esc(label)}</button>'
        for i, (key, label, _, _) in enumerate(specs)
    )
    panes = "".join(
        f'<div class="pane{" on" if i == 0 else ""}" id="p-{key}" data-group="g1">'
        f'<p class="h2note">{esc(note)}</p>{_table(rows, score_max)}</div>'
        for i, (key, _, note, rows) in enumerate(specs)
    )
    return f'<div class="tabs" data-group="g1">{tabs}</div>{panes}'


def _category_cards(rankings: dict) -> str:
    cards = []
    for c in rankings["best_in_category"]:
        b = c["best"]
        cards.append(
            f'<div class="card"><div class="lab">{icons.for_category(c["category"])}'
            f'{esc(c["category"])} · 共 {c["count"]} 款</div>'
            f'<div class="val">{esc(b["name"])}</div>'
            f'<div class="who">¥{fmt(b["price"], 0)} · {fmt(b["kcal"], 0)}kcal · 蛋白 '
            f'{fmt(b["protein"], 0)}g · 钠 {fmt(b["sodium"], 0)}mg · {fmt(b["score"], 1)} 分</div></div>'
        )
    return f'<div class="grid g2">{"".join(cards)}</div>'


def render(rankings: dict, meta: dict) -> str:
    score_max = max((x["score"] for x in rankings["all"]), default=100)
    floor = rankings.get("protein_floor", 5.0)
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")
    stats = meta.get("stats") or {}

    notice = ""
    if meta.get("demo"):
        notice = ('<div class="notice"><b>示例数据模式</b>：当前未配置 MCP Token，'
                  '以下为演示用示例估算值，非麦当劳官方实时数据。'
                  '配置 <code>MCD_MCP_TOKEN</code> 后重跑即切换为真实数据。</div>')

    cover = ""
    if stats:
        cover = (f"<span>营养库 {stats['nutrition_total']} 款 · 本店在售单品 "
                 f"{stats['menu_singles']} 款 · 精确匹配 {stats['matched']} 款</span>")
        if not meta.get("demo"):
            notice += (
                '<div class="notice"><b>关于样本量</b>：麦当劳营养库覆盖全时段餐品'
                f'（{stats["nutrition_total"]} 款，含早餐等），而门店菜单是'
                f'当前时段在售（{stats["menu_singles"]} 款单品，'
                f'已排除 {stats["menu_combo_excluded"]} 款套餐与周边）。'
                '两者按名称精确匹配后得到 '
                f'{stats["matched"]} 款 —— 未匹配的多为当前时段未供应或限定款，属正常现象。'
                '为保证价格准确，程序宁可少收录也不错配。</div>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>麦当劳营养红黑榜 · 蛋白质性价比计算器</title>
<meta name="description" content="把麦当劳菜单的营养数据与价格 join 起来，算出每一块钱能买到多少克蛋白质。">
<style>{CSS}</style>
</head>
<body>
{icons.sprite()}
<header><div class="wrap">
<h1>麦当劳营养红黑榜</h1>
<div class="sub">把营养数据和价格 join 起来 —— 你花的每一块钱，到底买到了多少克蛋白质？</div>
<div class="meta">
<span>样本 {meta['count']} 款餐品</span>
{cover}
<span>数据源：{esc(meta['source'])}</span>
{('<span>采集于 ' + esc(meta['captured']) + '</span>') if meta.get('captured') else ''}
<span>生成于 {now}</span>
<span>开源项目 <a href="{REPO_URL}" target="_blank" rel="noopener">york0307/mcd-protein-value</a></span>
</div>
</div></header>

<div class="wrap">
{notice}

<h2>先看结论</h2>
<p class="h2note">以下数字全部由营养数据与价格实时计算得出，公式见文末「算法说明」。</p>
<div class="grid g4">{_metric_cards(rankings)}</div>

<h2>三个反直觉发现</h2>
<p class="h2note">这些是这份榜单最值得转发的部分。</p>
{_insights(rankings)}

<h2>红榜 · 综合最优 Top {len(rankings['red_list'])}</h2>
<p class="h2note">综合蛋白密度、蛋白质性价比与钠负荷三项加权，满分 100。
仅统计蛋白 ≥ {floor:.0f}g 的餐品 —— 咖啡、可乐等本就不是蛋白质来源，
若按密度硬排会被极低热量饮品霸榜，结论失真。</p>
{_table(rankings['red_list'], score_max)}

<h2>黑榜 · 最该警惕 Top {len(rankings['black_list'])}</h2>
<p class="h2note">在蛋白 ≥ {floor:.0f}g 的餐品中，钠越高、蛋白密度越低，警惕指数越高。
不是不能吃，是要知道代价。已排除红榜餐品，避免同一款两榜都出现。</p>
{_table(rankings['black_list'], score_max)}

<h2>各品类最优解</h2>
<p class="h2note">只想看某一类该点什么，看这里。</p>
{_category_cards(rankings)}

<h2>四个专项榜</h2>
<p class="h2note">同一个餐品在不同目标下排名完全不同，切换查看。</p>
{_panes(rankings, score_max)}

<h2>全量数据</h2>
<p class="h2note">按综合分降序，共 {meta['count']} 款。</p>
{_table(rankings['all'], score_max)}

<h2>算法说明</h2>
<div class="method">
<h3>四项核心指标</h3>
<ul>
<li><code>蛋白质性价比</code> = 蛋白质(g) ÷ 价格(元) —— 健身人群视角</li>
<li><code>蛋白密度</code> = 蛋白质(g) ÷ 能量(kcal) × 100 —— 减脂期视角</li>
<li><code>热量性价比</code> = 能量(kcal) ÷ 价格(元) —— 预算有限视角</li>
<li><code>钠负荷</code> = 钠(mg) ÷ 2000mg —— 《中国居民膳食指南》每日上限</li>
</ul>
<h3>综合评分</h3>
<p><code>score = 0.40 × 归一(蛋白密度) + 0.35 × 归一(蛋白质性价比) + 0.25 × (1 − 归一(钠))</code></p>
<p>归一化采用当前数据集内的 min-max，因此评分是<b>相对排序</b>而非绝对评级，钠为惩罚项。</p>
<h3>两项防失真约束</h3>
<ul>
<li>蛋白类榜单设准入门槛<code>蛋白 ≥ {floor:.0f}g</code>。否则 13kcal 的浓缩咖啡
（蛋白 1g）密度可达 7.7，会霸榜 —— 它本就不是蛋白质来源。</li>
<li>套餐与周边（<code>三件套/四件套/套餐/玩具</code>等）已排除。
它们的营养数据是单品口径，用套餐价去比会严重低估单价。</li>
</ul>
<h3>为什么必须用 MCP</h3>
<p>营养数据里没有价格，菜单里没有营养成分。只有把 <code>list-nutrition-foods</code> 与
<code>query-meals</code> 两份数据 join 起来，才能算出「每元蛋白质」——这是单看任何一份数据都得不出的结论。</p>
</div>

<h2>这份榜单是开源的</h2>
<p class="h2note">数据不是手工录入的静态表，全部来自麦当劳官方 MCP 实时接口。</p>
<div class="cta">
<h3>觉得有用，给个 Star ⭐</h3>
<p>本项目参加 2026 麦当劳程序员创意开发大赛，榜单排名由仓库的公开 Star 数决定 —— 你的一颗 Star 就是一票。</p>
<div class="btns">
<a class="pri" href="{REPO_URL}" target="_blank" rel="noopener">⭐ Star 这个项目</a>
<a href="{REPO_URL}#readme" target="_blank" rel="noopener">查看源码与接入方式</a>
</div>
<div class="tip">价格随门店和时段浮动。想看你所在城市的榜单，clone 仓库、配好 Token 后跑
<code>python run.py --city 上海</code> 即可重新生成；没有 Token 也能用
<code>python run.py --demo</code> 先跑通全链路。</div>
</div>

<footer>
本页由开源项目 <b><a href="{REPO_URL}" target="_blank" rel="noopener">mcd-protein-value</a></b> 自动生成，
为麦当劳程序员节创意开发大赛参赛作品，<b>非麦当劳官方产品</b>。
数据仅供参考，不构成医疗或营养专业建议；餐品信息、价格及供应状态以麦当劳官方渠道的实时结果为准。
</footer>
</div>
<script>{JS}</script>
</body>
</html>
"""


def write_report(rankings: dict, meta: dict, path: str = "output/index.html") -> str:
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(rankings, meta))
    return path
