#!/usr/bin/env python3
"""餐品品类图标 —— 全部为本项目手绘 SVG。

为什么不用麦当劳官方餐品图
--------------------------
1. MCP 确实返回了官方图床 URL（menu-img.mcd.cn），但「接口给了 URL」≠
   「授权我在衍生作品里分发这些图片」。参赛声明要求素材已取得合法授权，
   这是说不清的灰度地带 —— 为一个装饰去冒合规风险，收益为负。
2. 外链会破坏「自包含单文件」这条底线：报告/对比器要能直接丢到任意静态托管、
   能离线打开、能截图传播，一旦图片来自外部域名，断网即破图。
3. base64 内嵌更糟：等于二次分发麦当劳的图片二进制，且体积从 20KB 涨到 MB 级。
4. 对核心洞察零贡献 —— 榜单的价值是「每元买到多少蛋白质」，照片不参与计算。

真正的痛点是**识别成本**
------------------------
「薄皮焦香V翅」这六个字，不看图不知道是哪款。解法不是照片，是**视觉锚点**：
给每个品类一个原创手绘图标，18px 下也能一眼区分。

所以这里的图标满足四条：
- 原创手绘（零版权风险）
- 内联 SVG symbol，全站只出现一次（体积可忽略）
- 无任何外部请求（保持零依赖）
- 18px 下靠形状+配色就能区分，不靠细节
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------- 图形定义
# viewBox 统一 24×24。配色沿用麦当劳红黄 + 食物本身的固有色，
# 保证在白底卡片和浅灰底表格上都清晰。

_SYMBOLS = {
    # 汉堡：芝麻面包 + 生菜 + 牛肉饼
    "burger": (
        '<path d="M2.6 10.4a9.5 6.4 0 0 1 18.8 0Z" fill="#F0A93C"/>'
        '<g fill="#FFF6E5"><circle cx="8.2" cy="8.3" r="1"/>'
        '<circle cx="12" cy="7.2" r="1"/><circle cx="15.8" cy="8.3" r="1"/></g>'
        '<rect x="2.6" y="10.4" width="18.8" height="2" rx=".9" fill="#7CB342"/>'
        '<rect x="2.6" y="12.4" width="18.8" height="2.6" rx="1" fill="#6B4423"/>'
        '<path d="M2.6 15.2h18.8v2.5a2.5 2.5 0 0 1-2.5 2.5H5.1a2.5 2.5 0 0 1-2.5-2.5Z" fill="#F0A93C"/>'
    ),
    # 厚牛堡：更高的面包 + 芝士瀑布 + 双层厚饼
    "beef": (
        '<path d="M2.8 8.6a9.2 6 0 0 1 18.4 0Z" fill="#F0A93C"/>'
        '<g fill="#FFF6E5"><circle cx="8.4" cy="6.6" r=".9"/>'
        '<circle cx="12" cy="5.6" r=".9"/><circle cx="15.6" cy="6.6" r=".9"/></g>'
        '<path d="M2.8 8.6h18.4l-1.7 2.3H4.5Z" fill="#FFC72C"/>'
        '<rect x="2.8" y="10.9" width="18.4" height="3.3" rx="1" fill="#6B4423"/>'
        '<rect x="2.8" y="14.2" width="18.4" height="1.5" rx=".75" fill="#FFC72C"/>'
        '<path d="M2.8 15.7h18.4v2.4a2.4 2.4 0 0 1-2.4 2.4H5.2a2.4 2.4 0 0 1-2.4-2.4Z" fill="#F0A93C"/>'
    ),
    # 卷：斜置的卷饼，左端深色收口
    "wrap": (
        '<g transform="rotate(-38 12 12)">'
        '<rect x="3.6" y="8.4" width="16.8" height="7.2" rx="3.6" fill="#F3D49A"/>'
        '<circle cx="7.2" cy="12" r="3.6" fill="#DFA955"/>'
        '<path d="M10.6 12h6.4" stroke="#C9964A" stroke-width="1.3" stroke-linecap="round"/>'
        "</g>"
    ),
    # 炸鸡：鸡腿（两个圆叠出水滴状肉块 + 骨头）
    "chicken": (
        '<path d="M11.8 14.6 7.6 18.8" stroke="#F4E7CE" stroke-width="2.5" '
        'stroke-linecap="round" fill="none"/>'
        '<circle cx="6.1" cy="19.9" r="2" fill="#F4E7CE"/>'
        '<circle cx="15.7" cy="8.9" r="5.5" fill="#E3A03A"/>'
        '<circle cx="13.3" cy="12.5" r="3.7" fill="#E3A03A"/>'
    ),
    # 小食甜品：冰淇淋甜筒（本品类里就有圆筒冰淇淋）
    "dessert": (
        '<circle cx="9.4" cy="8.6" r="3.9" fill="#FFF1DC"/>'
        '<circle cx="14.6" cy="8.6" r="3.9" fill="#FFF1DC"/>'
        '<path d="M6 11.4h12l-6 10.2Z" fill="#E8B36A"/>'
        '<g stroke="#D49A4C" stroke-width="1.1" stroke-linecap="round">'
        '<path d="M8.2 14.6l1.6 2.6"/><path d="M12 14.6v2.6"/>'
        '<path d="M15.8 14.6l-1.6 2.6"/></g>'
    ),
    # 饮品：带吸管与品牌腰线的冷饮杯
    "drink": (
        '<path d="M5.6 7.6h12.8l-1.4 13.2a1.6 1.6 0 0 1-1.6 1.4H8.6a1.6 1.6 0 0 1-1.6-1.4Z" fill="#E9F0F4"/>'
        '<path d="M6.4 12.4h11.2l-.5 4H6.9Z" fill="#DA291C"/>'
        '<rect x="4.6" y="4.8" width="14.8" height="3" rx="1.5" fill="#C9D5DC"/>'
        '<path d="M15.8 4.8 18.8 1.4" stroke="#DA291C" stroke-width="2" stroke-linecap="round"/>'
    ),
    # 麦咖啡：马克杯 + 咖啡液面 + 热气
    "cafe": (
        '<path d="M4.4 8.2h11.2v7.4a3.4 3.4 0 0 1-3.4 3.4H7.8a3.4 3.4 0 0 1-3.4-3.4Z" fill="#F7F3EC"/>'
        '<path d="M4.4 8.2h11.2v3.4H4.4Z" fill="#6F4E37"/>'
        '<path d="M15.6 9.6h1.3a2.7 2.7 0 0 1 0 5.4h-1.3" fill="none" '
        'stroke="#F7F3EC" stroke-width="1.7"/>'
        '<g fill="none" stroke="#CFC8BE" stroke-width="1.5" stroke-linecap="round">'
        '<path d="M8.2 3.2c0 1.3 1.3 1.1 1.3 2.4"/><path d="M12.4 3c0 1.3 1.3 1.1 1.3 2.4"/></g>'
    ),
    # 兜底：未识别品类的盘子
    "plate": (
        '<circle cx="12" cy="12" r="9" fill="none" stroke="#C9C4BC" stroke-width="1.6"/>'
        '<circle cx="12" cy="12" r="3.4" fill="#C9C4BC"/>'
    ),
}

# 菜单分类名 → 图标。分类名来自 MCP，带空格、™ 等噪声，匹配时统一压平。
_CATEGORY_RULES: list[tuple[str, str]] = [
    ("巨无霸牛鱼肉堡", "burger"),
    ("安格斯MAX厚牛堡", "beef"),
    ("鸡肉汉堡卷", "wrap"),
    ("炸鸡", "chicken"),
    ("小食甜品其他", "dessert"),
    ("饮品", "drink"),
    ("麦咖啡", "cafe"),
]

# 关键词兜底：新品类出现时也能给出合理的图标，而不是全部掉到盘子
_KEYWORD_RULES: list[tuple[str, str]] = [
    ("咖啡", "cafe"),
    ("饮", "drink"),
    ("鸡", "chicken"),
    ("堡", "burger"),
    ("卷", "wrap"),
    ("甜品", "dessert"),
    ("小食", "dessert"),
]

_NOISE = re.compile(r"[\s™®©*/、·\-—]+")


def _flat(s: str) -> str:
    """压平分类名：去空格与商标符号，便于稳定匹配。"""
    return _NOISE.sub("", str(s or ""))


def icon_id(category: str | None) -> str:
    """分类名 → 图标 id。匹配不到时按关键词兜底，再不行返回 plate。"""
    n = _flat(category)
    if not n:
        return "plate"
    for key, iid in _CATEGORY_RULES:
        k = _flat(key)
        if n == k or k in n or n in k:
            return iid
    for key, iid in _KEYWORD_RULES:
        if key in n:
            return iid
    return "plate"


def sprite() -> str:
    """全站图标雪碧，只需在 <body> 开头注入一次。"""
    body = "".join(
        f'<symbol id="ic-{k}" viewBox="0 0 24 24">{v}</symbol>'
        for k, v in _SYMBOLS.items()
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">{body}</svg>'


def svg(iid: str, cls: str = "ic") -> str:
    """引用雪碧里的图标。"""
    return f'<svg class="{cls}" aria-hidden="true"><use href="#ic-{iid}"/></svg>'


def for_category(category: str | None, cls: str = "ic") -> str:
    return svg(icon_id(category), cls)
