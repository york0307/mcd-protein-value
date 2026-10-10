#!/usr/bin/env python3
"""数字格式化 —— 只做一件事：**让 Python 端和 JS 端算出同一个数**。

为什么需要单独一个模块
----------------------
同一个项目里，同一款餐品的价格会在三处被渲染：

1. 报告（Python 生成）
2. 对比器顶部的静态榜单表（Python 生成）
3. 对比器的对比卡片（浏览器里 JS 算）

三处只要有一处舍入规则不同，用户就会看到「巨无霸 ¥26」和「巨无霸 ¥27」
同时存在 —— 而在一份讲数据的榜单里，这会被直接当成数据错误。

根因是 Python 的 `f"{26.5:.0f}"` 用的是**银行家舍入**（26.5 → 26），
而 JS 的 `Math.round(26.5)` 是**半进位**（→ 27）。20 款餐品里有 7 款是
`.5` 结尾的价，全部命中这个差异。

因此规则只有一条：**nd=0 时一律半进位，与 JS Math.round 对齐。**
前端 `compare.py` 里的 `pr()` / `n0()` 必须保持 `Math.round`，改这两处要同步。
"""

from __future__ import annotations

import math


def r0(v) -> int:
    """半进位取整，等价于 JS 的 Math.round（仅用于非负价格/热量/钠）。"""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return 0
    if x >= 0:
        return int(math.floor(x + 0.5))
    return -int(math.floor(-x + 0.5))


def fmt(v, nd: int = 1) -> str:
    """格式化数字。nd=0 时走半进位，其余情况保留 nd 位小数。"""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "-"
    if nd <= 0:
        return str(r0(x))
    return f"{x:.{nd}f}"
