#!/usr/bin/env python3
"""麦当劳 MCP 响应解析器。

服务端有两种「非标准」返回形态，都在这里收敛成 Python 对象：

1. **文本包裹型** —— 返回的是一段 Markdown 说明 + 内嵌 JSON，例如
   `# API Response Information ... ## Original Response\\n\\n{...}`
   需要先剥掉说明文字再 raw_decode。

2. **自定义表格型** —— `list-nutrition-foods` 的 `data` 字段不是数组，而是
   形如 `[160]{productName,energyKcal,...}:` 后跟若干 CSV 行的自定义文本：
   ```
   [160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:
     猪柳麦满分,null,1288,308,16,16,24,781,213
     猪柳蛋麦满分,null,1618,387,23,21,25,846,243
   ```
   需要按表头切分。
"""

from __future__ import annotations

import json
import re
from typing import Any

MARKER = "## Original Response"
TABLE_HEAD = re.compile(r"\[(\d+)\]\s*\{([^}]*)\}\s*:")


def extract_payload(obj: Any) -> dict | None:
    """从任意包裹形态里剥出业务 JSON。"""
    if isinstance(obj, dict):
        # 已经是结构化对象，但业务体可能藏在 data 里
        return obj
    if not isinstance(obj, str):
        return None

    text = obj
    start = 0
    idx = text.find(MARKER)
    if idx >= 0:
        start = idx + len(MARKER)

    pos = text.find("{", start)
    if pos < 0:
        return None
    dec = json.JSONDecoder()
    try:
        data, _ = dec.raw_decode(text[pos:])
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _cell(v: str) -> Any:
    v = v.strip()
    if v in ("", "null", "NULL", "None"):
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def parse_table(text: str) -> list[dict]:
    """解析 `[N]{字段}:` + CSV 行的自定义表格文本。"""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    head_pos = None
    fields: list[str] = []
    for i, ln in enumerate(lines):
        m = TABLE_HEAD.search(ln)
        if m:
            head_pos = i
            fields = [f.strip() for f in m.group(2).split(",")]
            break
    if head_pos is None:
        return []

    rows = []
    for ln in lines[head_pos + 1:]:
        parts = ln.split(",")
        if len(parts) < len(fields):
            continue
        rows.append({fields[i]: _cell(parts[i]) for i in range(len(fields))})
    return rows


def parse_nutrition(obj: Any) -> list[dict]:
    """解析营养数据 → 规范字段列表。"""
    payload = extract_payload(obj)
    if not payload:
        return []
    data = payload.get("data")
    if isinstance(data, str):
        raw = parse_table(data)
    elif isinstance(data, list):
        raw = data
    else:
        return []

    out = []
    for r in raw:
        name = r.get("productName") or r.get("name")
        if not name:
            continue
        out.append({
            "code": None,
            "name": str(name).strip(),
            "category": None,
            "price": None,
            "kcal": r.get("energyKcal") or 0,
            "protein": r.get("protein") or 0,
            "fat": r.get("fat") or 0,
            "carb": r.get("carbohydrate") or 0,
            "sodium": r.get("sodium") or 0,
            "calcium": r.get("calcium") or 0,
        })
    return out


def parse_menu(obj: Any) -> list[dict]:
    """解析菜单数据 → [{code, name, price, category}]。"""
    payload = extract_payload(obj)
    if not payload:
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []

    meals_map = data.get("meals") or {}
    cat_of: dict[str, str] = {}
    for cat in data.get("categories") or []:
        cname = cat.get("name") or "未分类"
        for m in cat.get("meals") or []:
            code = m.get("code")
            if code:
                cat_of.setdefault(str(code), cname)

    out = []
    for code, detail in meals_map.items():
        if not isinstance(detail, dict):
            continue
        name = detail.get("name")
        if not name:
            continue
        # 分类名里可能带换行（服务端原样返回），统一压平
        cat = " ".join(str(cat_of.get(str(code), "未分类")).split())
        out.append({
            "code": str(code),
            "name": " ".join(str(name).split()),
            "category": cat,
            "price": detail.get("currentPrice"),
        })
    return out


# ---------------- 名称归一与匹配 ----------------

_PUNCT = re.compile(r"[\s（）()\[\]【】·、,，\-—_/\\]+")
_FULL2HALF = str.maketrans({
    "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
    "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
    "（": "(", "）": ")", "　": " ",
})

# 套餐/周边的价格与单品营养数据不可比，必须排除
COMBO_PAT = re.compile(r"(套餐|件套|双人餐|全家桶|组合|周边|玩具|盲盒|兑换券|礼品卡|早餐卡|麦金卡)")

# 规格修饰词：用于生成「基础名」候选，如 '中薯条'→'薯条'、'麦乐鸡5块'→'麦乐鸡'
SIZE_LEAD = re.compile(r"^(超大|大杯|中杯|小杯|迷你|大|中|小)")
QTY_TAIL = re.compile(r"(\d+\s*(块|片|只|个|支|杯))+$")


def is_combo(name: str) -> bool:
    return bool(COMBO_PAT.search(str(name or "")))


def norm_name(s: str) -> str:
    """名称归一化，用于跨数据源匹配。

    例：'麦乐鸡（5块）' 与 '麦乐鸡5块' → 同为 '麦乐鸡5块'
    """
    s = str(s or "").translate(_FULL2HALF)
    s = _PUNCT.sub("", s)
    return s.lower()


def base_forms(name: str) -> set[str]:
    """基础名候选：去掉规格修饰后的等价写法。"""
    n = norm_name(name)
    forms = {n}
    stripped = SIZE_LEAD.sub("", n)
    forms.add(stripped)
    forms.add(QTY_TAIL.sub("", stripped))
    forms.discard("")
    return forms - {n}


def join_by_name(nutrition: list[dict], menu: list[dict]) -> tuple[list[dict], list[str], dict]:
    """按归一化名称把营养数据与菜单价格 join 起来。

    匹配分两级，都要求**双向唯一**：

    1. 精确匹配：归一化名完全相等。
    2. 基础名匹配：去掉规格修饰（'中薯条'→'薯条'、'麦乐鸡5块'→'麦乐鸡'）后再比对，
       但仅当该菜单名**只被一个**营养条目命中时才采纳。

    为什么不做「互为子串」的模糊匹配：实测 '吉士汉堡包' 会命中 '吉士汉堡包套餐'、
    '大杯玉米杯' 和 '小杯玉米杯' 会同时命中 '玉米杯'，导致价格张冠李戴。
    同理，'薯条' 同时被 大/中/小/迷你 四个规格命中，会被唯一性约束挡掉。
    公开榜单里错价的代价远高于少收录几款，宁可保守。
    """
    singles = [m for m in menu if not is_combo(m["name"])]
    index: dict[str, dict] = {}
    for m in singles:
        index.setdefault(norm_name(m["name"]), m)

    # 第一级：精确匹配
    merged, unmatched, fuzzy = [], [], []
    for n in nutrition:
        hit = index.get(norm_name(n["name"]))
        if hit is not None:
            merged.append((n, hit, "exact"))
        else:
            fuzzy.append(n)

    # 第二级：基础名匹配，先统计每个菜单名被多少个营养条目命中
    claims: dict[str, list[dict]] = {}
    for n in fuzzy:
        for form in base_forms(n["name"]):
            if form in index:
                claims.setdefault(form, []).append(n)

    loose_hits: dict[str, dict] = {}
    for form, group in claims.items():
        if len(group) == 1:  # 双向唯一才采纳
            loose_hits[group[0]["name"]] = index[form]

    for n in fuzzy:
        hit = loose_hits.get(n["name"])
        if hit is not None:
            merged.append((n, hit, "base"))
        else:
            unmatched.append(n["name"])

    rows = []
    for n, hit, how in merged:
        row = dict(n)
        row["code"] = hit.get("code")
        row["category"] = hit.get("category") or "未分类"
        row["menu_name"] = hit.get("name")
        row["match"] = how
        try:
            row["price"] = float(str(hit.get("price")).replace("¥", "").strip() or 0)
        except (TypeError, ValueError):
            row["price"] = 0.0
        rows.append(row)

    zero = [r["name"] for r in rows if r["price"] <= 0]
    rows = [r for r in rows if r["price"] > 0]

    # 营养库里存在同名条目（如 '纯牛奶' 与 '纯牛奶（盒装）'），
    # 归一化后会同时命中同一个菜单项，必须按菜单编码去重，否则榜单会出现重复行
    seen: set[str] = set()
    deduped = []
    for r in rows:
        key = str(r.get("code") or norm_name(r.get("menu_name") or r["name"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    dupes = len(rows) - len(deduped)
    rows = deduped

    stats = {
        "nutrition_total": len(nutrition),
        "menu_total": len(menu),
        "menu_singles": len(singles),
        "menu_combo_excluded": len(menu) - len(singles),
        "matched": len(rows),
        "matched_exact": sum(1 for r in rows if r["match"] == "exact"),
        "matched_base": sum(1 for r in rows if r["match"] == "base"),
        "unmatched": len(unmatched),
        "zero_price": len(zero),
        "duplicates_removed": dupes,
    }
    return rows, unmatched, stats
