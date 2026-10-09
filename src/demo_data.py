#!/usr/bin/env python3
"""内置示例数据 —— 仅用于在没有 MCP Token 时跑通全链路并演示效果。

⚠️ 重要声明
-----------
本文件的营养数值为**公开常识量级的示例估算值**，价格为中国大陆地区常见参考价，
**不代表麦当劳官方实时数据**，不可用于任何实际营养决策。

一旦配置了真实 MCD_MCP_TOKEN，程序会自动切换到
`list-nutrition-foods` + `query-meals` 的真实数据，本文件不再参与计算。
"""

# 字段：code, name, category, price(元), kcal, protein(g), fat(g), carb(g), sodium(mg), calcium(mg)
DEMO_NUTRITION: list[dict] = [
    # ---- 汉堡 ----
    {"code": "MCD001", "name": "巨无霸", "category": "汉堡", "price": 24,
     "kcal": 550, "protein": 26, "fat": 30, "carb": 46, "sodium": 1050, "calcium": 200},
    {"code": "MCD002", "name": "麦香鱼", "category": "汉堡", "price": 15,
     "kcal": 400, "protein": 15, "fat": 18, "carb": 45, "sodium": 650, "calcium": 150},
    {"code": "MCD003", "name": "麦辣鸡腿堡", "category": "汉堡", "price": 21,
     "kcal": 570, "protein": 24, "fat": 32, "carb": 48, "sodium": 1200, "calcium": 120},
    {"code": "MCD004", "name": "板烧鸡腿堡", "category": "汉堡", "price": 20,
     "kcal": 500, "protein": 27, "fat": 22, "carb": 45, "sodium": 900, "calcium": 160},
    {"code": "MCD005", "name": "麦香鸡", "category": "汉堡", "price": 13,
     "kcal": 350, "protein": 14, "fat": 16, "carb": 38, "sodium": 600, "calcium": 100},
    {"code": "MCD006", "name": "双层吉士汉堡", "category": "汉堡", "price": 15,
     "kcal": 440, "protein": 22, "fat": 21, "carb": 41, "sodium": 880, "calcium": 250},
    {"code": "MCD007", "name": "吉士汉堡", "category": "汉堡", "price": 10,
     "kcal": 300, "protein": 15, "fat": 12, "carb": 34, "sodium": 620, "calcium": 180},
    {"code": "MCD008", "name": "汉堡包", "category": "汉堡", "price": 8,
     "kcal": 250, "protein": 12, "fat": 9, "carb": 31, "sodium": 480, "calcium": 100},
    {"code": "MCD009", "name": "双层牛柳堡", "category": "汉堡", "price": 22,
     "kcal": 520, "protein": 30, "fat": 26, "carb": 42, "sodium": 980, "calcium": 180},

    # ---- 小食 ----
    {"code": "MCD010", "name": "薯条（大）", "category": "小食", "price": 12,
     "kcal": 500, "protein": 6, "fat": 25, "carb": 63, "sodium": 350, "calcium": 20},
    {"code": "MCD011", "name": "薯条（中）", "category": "小食", "price": 10,
     "kcal": 340, "protein": 4, "fat": 17, "carb": 43, "sodium": 240, "calcium": 15},
    {"code": "MCD012", "name": "麦乐鸡（5块）", "category": "小食", "price": 13,
     "kcal": 230, "protein": 13, "fat": 14, "carb": 12, "sodium": 500, "calcium": 30},
    {"code": "MCD013", "name": "麦辣鸡翅（2块）", "category": "小食", "price": 13,
     "kcal": 230, "protein": 17, "fat": 15, "carb": 8, "sodium": 700, "calcium": 25},
    {"code": "MCD014", "name": "玉米杯", "category": "小食", "price": 8,
     "kcal": 90, "protein": 3, "fat": 1, "carb": 19, "sodium": 10, "calcium": 5},
    {"code": "MCD015", "name": "蔬菜沙拉", "category": "小食", "price": 12,
     "kcal": 60, "protein": 2, "fat": 3, "carb": 6, "sodium": 120, "calcium": 60},

    # ---- 早餐 ----
    {"code": "MCD016", "name": "吉士蛋麦满分", "category": "早餐", "price": 12,
     "kcal": 300, "protein": 15, "fat": 13, "carb": 30, "sodium": 700, "calcium": 220},
    {"code": "MCD017", "name": "猪柳蛋麦满分", "category": "早餐", "price": 14,
     "kcal": 380, "protein": 19, "fat": 20, "carb": 31, "sodium": 820, "calcium": 200},
    {"code": "MCD018", "name": "原味板烧鸡腿麦满分", "category": "早餐", "price": 13,
     "kcal": 340, "protein": 20, "fat": 14, "carb": 33, "sodium": 780, "calcium": 150},
    {"code": "MCD019", "name": "火腿扒麦满分", "category": "早餐", "price": 11,
     "kcal": 280, "protein": 16, "fat": 11, "carb": 30, "sodium": 690, "calcium": 180},

    # ---- 饮料 ----
    {"code": "MCD020", "name": "冰美式（大）", "category": "饮料", "price": 12,
     "kcal": 15, "protein": 0, "fat": 0, "carb": 3, "sodium": 10, "calcium": 10},
    {"code": "MCD021", "name": "拿铁（大）", "category": "饮料", "price": 18,
     "kcal": 150, "protein": 8, "fat": 7, "carb": 12, "sodium": 110, "calcium": 280},
    {"code": "MCD022", "name": "纯牛奶", "category": "饮料", "price": 8,
     "kcal": 130, "protein": 8, "fat": 7, "carb": 12, "sodium": 120, "calcium": 300},
    {"code": "MCD023", "name": "可口可乐（中）", "category": "饮料", "price": 9,
     "kcal": 210, "protein": 0, "fat": 0, "carb": 53, "sodium": 25, "calcium": 0},
    {"code": "MCD024", "name": "零度可乐（中）", "category": "饮料", "price": 9,
     "kcal": 2, "protein": 0, "fat": 0, "carb": 0, "sodium": 30, "calcium": 0},

    # ---- 甜品 ----
    {"code": "MCD025", "name": "香芋派", "category": "甜品", "price": 9,
     "kcal": 260, "protein": 3, "fat": 14, "carb": 31, "sodium": 220, "calcium": 30},
    {"code": "MCD026", "name": "麦旋风（奥利奥）", "category": "甜品", "price": 13,
     "kcal": 300, "protein": 5, "fat": 11, "carb": 46, "sodium": 160, "calcium": 150},
    {"code": "MCD027", "name": "草莓新地", "category": "甜品", "price": 10,
     "kcal": 270, "protein": 4, "fat": 8, "carb": 45, "sodium": 130, "calcium": 140},
]

DEMO_MENU: list[dict] = [
    {"code": item["code"], "name": item["name"], "price": item["price"]}
    for item in DEMO_NUTRITION
]


def load_demo() -> list[dict]:
    """返回演示用合并数据（已含营养与价格）。"""
    return [dict(x) for x in DEMO_NUTRITION]
