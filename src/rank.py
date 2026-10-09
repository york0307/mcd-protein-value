#!/usr/bin/env python3
"""指标计算与榜单排序。

四项核心指标（每个都可追溯到原始字段，公式公开可复核）
------------------------------------------------------
1. 蛋白质性价比   protein_per_yuan = 蛋白质(g) / 价格(元)
      → 回答「花一块钱能买到多少克蛋白质」，健身人群最关心。

2. 蛋白密度       protein_density = 蛋白质(g) / 能量(kcal) × 100
      → 回答「每吃 100 大卡能拿到多少克蛋白质」，减脂期最关心。
      → 巨无霸 26g/550kcal ≈ 4.7；麦辣鸡翅 17g/230kcal ≈ 7.4。

3. 热量性价比     kcal_per_yuan = 能量(kcal) / 价格(元)
      → 回答「花一块钱能买到多少大卡」，预算有限时关心。

4. 钠负荷         sodium_pct = 钠(mg) / 2000mg
      → 2000mg 为《中国居民膳食指南》建议的每日钠摄入上限。

综合评分（面向「想吃得干净又不想花冤枉钱」的默认人群）
      score = 0.40 × 归一(蛋白密度) + 0.35 × 归一(蛋白质性价比) + 0.25 × (1 − 归一(钠))
      → 满分 100。钠是惩罚项，故用 1 − 归一值。

归一化采用当前数据集内的 min-max，因此评分是**相对排序**而非绝对评级。
"""

from __future__ import annotations

from typing import Any, Iterable

SODIUM_DAILY_LIMIT_MG = 2000  # 中国居民膳食指南建议上限

# 蛋白类榜单的准入门槛：低于此值的餐品（咖啡、可乐等）本质上不是蛋白质来源，
# 若仅按「蛋白密度」排序会被极低热量饮品霸榜（13kcal 的浓缩咖啡密度可达 7.7），
# 结论失真。故红榜与蛋白密度榜只统计蛋白 ≥ 5g 的餐品。
MIN_PROTEIN_G = 5.0

# 综合评分权重
W_PROTEIN_DENSITY = 0.40
W_PROTEIN_VALUE = 0.35
W_SODIUM_PENALTY = 0.25


def _num(v: Any) -> float:
    """尽力把各种形态的数值（含 '550千卡'、'26.0g'）转成 float。"""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    buf = ""
    seen_dot = False
    for ch in s:
        if ch.isdigit():
            buf += ch
        elif ch == "." and not seen_dot:
            buf += ch
            seen_dot = True
        elif buf:
            break
    try:
        return float(buf) if buf else 0.0
    except ValueError:
        return 0.0


def compute_metrics(item: dict) -> dict:
    """给单条餐品补全派生指标。"""
    price = _num(item.get("price"))
    kcal = _num(item.get("kcal"))
    protein = _num(item.get("protein"))
    sodium = _num(item.get("sodium"))

    protein_per_yuan = protein / price if price > 0 else 0.0
    kcal_per_yuan = kcal / price if price > 0 else 0.0
    protein_density = (protein / kcal * 100) if kcal > 0 else 0.0
    sodium_pct = sodium / SODIUM_DAILY_LIMIT_MG

    out = dict(item)
    out.update({
        "price": price,
        "kcal": kcal,
        "protein": protein,
        "sodium": sodium,
        "protein_per_yuan": round(protein_per_yuan, 3),
        "kcal_per_yuan": round(kcal_per_yuan, 1),
        "protein_density": round(protein_density, 2),
        "sodium_pct": round(sodium_pct, 3),
    })
    return out


def _minmax(values: list[float]) -> list[float]:
    """min-max 归一化；全等时返回 0.5 避免除零。"""
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def score_all(items: list[dict]) -> list[dict]:
    """计算综合评分与警惕指数，返回按分数降序的新列表。"""
    if not items:
        return []

    metrics = [compute_metrics(x) for x in items]
    n = len(metrics)

    d_norm = _minmax([m["protein_density"] for m in metrics])
    v_norm = _minmax([m["protein_per_yuan"] for m in metrics])
    s_norm = _minmax([m["sodium"] for m in metrics])

    for i, m in enumerate(metrics):
        m["score"] = round(
            100 * (W_PROTEIN_DENSITY * d_norm[i]
                   + W_PROTEIN_VALUE * v_norm[i]
                   + W_SODIUM_PENALTY * (1 - s_norm[i])), 1)
        # 警惕指数：钠越高、蛋白密度越低 → 越该谨慎
        m["caution"] = round(100 * (0.6 * s_norm[i] + 0.4 * (1 - d_norm[i])), 1)
        m["rank"] = 0

    metrics.sort(key=lambda x: x["score"], reverse=True)
    for i, m in enumerate(metrics, 1):
        m["rank"] = i
    return metrics


def top(items: Iterable[dict], key: str, n: int = 8, desc: bool = True) -> list[dict]:
    return sorted(items, key=lambda x: x.get(key, 0), reverse=desc)[:n]


def best_in_category(items: list[dict]) -> list[dict]:
    """每个品类的最优解 —— 这部分最容易被截图传播。"""
    buckets: dict[str, list[dict]] = {}
    for it in items:
        buckets.setdefault(it.get("category") or "其他", []).append(it)
    out = []
    for cat, group in buckets.items():
        winner = max(group, key=lambda x: x.get("score", 0))
        out.append({"category": cat, "count": len(group), "best": winner})
    out.sort(key=lambda x: x["best"]["score"], reverse=True)
    return out


def build_rankings(items: list[dict]) -> dict:
    """产出报告所需的全部榜单。"""
    scored = score_all(items)
    # 蛋白类榜单设准入门槛，避免极低热量饮品靠分母优势霸榜
    eligible = [x for x in scored if x.get("protein", 0) >= MIN_PROTEIN_G] or scored
    red_list = eligible[:8]
    # 黑榜同样只在「够格当蛋白质来源」的餐品里选：
    # 锡兰红茶这类 0 蛋白饮品会因蛋白密度为 0 被判高警惕，
    # 但它钠也是 0，放进「最该警惕」显然不合理。
    # 同时排除已进红榜的餐品，避免同一款两榜都出现（读者会当成 bug）。
    red_names = {x["name"] for x in red_list}
    black_pool = [x for x in eligible if x["name"] not in red_names]
    return {
        "all": scored,
        "red_list": red_list,                                        # 综合红榜
        "black_list": top(black_pool, "caution", 8),                 # 钠/蛋白结构黑榜
        "by_protein_value": top(eligible, "protein_per_yuan", 8),    # 蛋白质性价比
        "by_protein_density": top(eligible, "protein_density", 8),   # 减脂友好
        "by_kcal_value": top(scored, "kcal_per_yuan", 8),            # 饱腹性价比
        "by_sodium": top(scored, "sodium", 8),                       # 钠警戒
        "best_in_category": best_in_category(scored),
        "protein_floor": MIN_PROTEIN_G,
    }


# ------------------------------------------------------------------
# 真实数据适配：把 MCP 原始记录映射为本项目规范字段
# ------------------------------------------------------------------

FIELD_CANDIDATES = {
    "code": ("code", "mealCode", "foodCode", "itemCode", "id", "餐品编码", "编码", "商品编码"),
    "name": ("name", "foodName", "mealName", "itemName", "title", "餐品名称", "名称", "商品名称"),
    "category": ("category", "categoryName", "type", "tag", "分类", "品类"),
    "price": ("price", "sellPrice", "salePrice", "amount", "价格", "售价", "单价"),
    "kcal": ("kcal", "energy", "calories", "calorie", "能量", "热量", "千卡"),
    "protein": ("protein", "蛋白质", "蛋白"),
    "fat": ("fat", "脂肪"),
    "carb": ("carb", "carbohydrate", "碳水化合物", "碳水"),
    "sodium": ("sodium", "na", "钠"),
    "calcium": ("calcium", "ca", "钙"),
}


def normalize(raw: list[dict], default_category: str = "未分类") -> list[dict]:
    """用候选字段名把任意 schema 的原始记录收敛成规范结构。

    若字段对不上（例如服务端改版），返回的结果里对应字段会是 0，
    此时应去 data/raw/ 里看原始响应并补充 FIELD_CANDIDATES。
    """
    from mcd_client import pick

    out = []
    for rec in raw:
        row = {}
        for field, candidates in FIELD_CANDIDATES.items():
            row[field] = pick(rec, *candidates)
        row["name"] = row.get("name") or "未知餐品"
        row["category"] = row.get("category") or default_category
        for numeric in ("price", "kcal", "protein", "fat", "carb", "sodium", "calcium"):
            row[numeric] = _num(row.get(numeric))
        out.append(row)
    return out


def merge(nutrition: list[dict], menu: list[dict]) -> list[dict]:
    """把营养数据与菜单价格 join 起来 —— 这是本项目「非 MCP 不可」的关键一步。

    单看营养数据没有价格，单看菜单没有营养成分，
    只有join之后才能算出「每元蛋白质」。
    """
    price_by_code = {str(m.get("code")): _num(m.get("price")) for m in menu if m.get("code")}
    price_by_name = {str(m.get("name")): _num(m.get("price")) for m in menu if m.get("name")}

    merged = []
    for item in nutrition:
        code = str(item.get("code") or "")
        name = str(item.get("name") or "")
        price = _num(item.get("price"))
        if price <= 0:
            price = price_by_code.get(code) or price_by_name.get(name) or 0.0
        row = dict(item)
        row["price"] = price
        merged.append(row)

    # 价格缺失的条目无法参与性价比计算，直接剔除并让上层提示
    return [x for x in merged if x["price"] > 0]
