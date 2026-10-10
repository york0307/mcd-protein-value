#!/usr/bin/env python3
"""命令行入口：生成麦当劳营养红黑榜。

    # 有 Token → 拉真实数据（默认到店取餐场景）
    export MCD_MCP_TOKEN="..."
    python run.py --city 南京 --keyword 麦当劳

    # 直接指定门店，跳过门店搜索
    python run.py --store-code 1990346

    # 没 Token → 用内置示例数据跑通全链路并预览效果
    python run.py --demo

    # 保存 MCP 原始响应，便于排查服务端结构变化
    python run.py --dump-raw

    # 从快照重放（午市样本最全，线上报告固定用它，避免早/晚市样本变形）
    python run.py --replay data/raw/nutrition_20261009_145325.json \
                           data/raw/probe_meals_20261009_145524.json
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import demo_data  # noqa: E402
import mcd_parse  # noqa: E402
import rank  # noqa: E402
import report  # noqa: E402

DEFAULT_CITY = os.environ.get("MCD_CITY", "南京")
DEFAULT_KEYWORD = os.environ.get("MCD_KEYWORD", "麦当劳")


def pick_store(client, city: str, keyword: str, dump: bool) -> dict:
    """查询附近门店，返回第一个可用门店。"""
    raw = client.call_tool("query-nearby-stores",
                           {"beType": 1, "searchType": 2, "city": city, "keyword": keyword})
    if dump:
        from mcd_client import dump_raw
        print(f"    原始响应已保存：{dump_raw(raw, 'stores')}")

    payload = mcd_parse.extract_payload(raw) or {}
    data = payload.get("data")
    if payload.get("code") not in (None, 200) or not isinstance(data, list) or not data:
        msg = payload.get("message") or "无结果"
        raise RuntimeError(f"门店查询失败：{msg}（试试换 --city / --keyword）")

    open_stores = [s for s in data if s.get("businessStatus")]
    store = (open_stores or data)[0]
    print(f"[✓] 门店：{store.get('storeName')}"
          f"（storeCode={store.get('storeCode')}，{store.get('address', '')[:22]}）")
    return store


def load_live(dump: bool, city: str, keyword: str, store_code: str | None):
    """走 MCP 真实数据。"""
    from mcd_client import McpClient, dump_raw

    client = McpClient()
    info = client.initialize()
    srv = info.get("serverInfo", {})
    print(f"[✓] 已连接 {srv.get('name', 'mcd-mcp')} v{srv.get('version', '?')}")

    if store_code:
        code, store_name = store_code, f"门店 {store_code}"
        print(f"[*] 使用指定门店 storeCode={code}")
    else:
        store = pick_store(client, city, keyword, dump)
        code, store_name = store.get("storeCode"), store.get("storeName")
        if not code:
            raise RuntimeError("门店缺少 storeCode")

    print("[*] 拉取营养数据 list-nutrition-foods ...")
    nutri_raw = client.fetch_nutrition()
    print(f"[*] 拉取菜单价格 query-meals (storeCode={code}) ...")
    menu_raw = client.fetch_menu(code)

    if dump:
        print(f"    原始响应已保存：{dump_raw(nutri_raw, 'nutrition')}")
        print(f"    原始响应已保存：{dump_raw(menu_raw, 'menu')}")

    nutri = mcd_parse.parse_nutrition(nutri_raw)
    menu = mcd_parse.parse_menu(menu_raw)
    print(f"[✓] 营养 {len(nutri)} 条 / 菜单 {len(menu)} 条")

    if not nutri or not menu:
        raise RuntimeError(
            "解析后数据为空。请加 --dump-raw 后查看 data/raw/ 中的原始响应结构是否已变化。"
        )

    merged, unmatched, stats = mcd_parse.join_by_name(nutri, menu)
    print(f"[✓] 精确匹配 {stats['matched']} 条"
          f"（套餐/周边排除 {stats['menu_combo_excluded']} 条，未匹配 {stats['unmatched']} 条）")

    if not merged:
        raise RuntimeError(
            "营养数据与菜单无法按名称匹配，无法计算性价比。请 --dump-raw 检查两份数据的命名差异。"
        )
    if unmatched:
        print(f"    [i] 未匹配多为当前时段未供应的餐品（如早餐），非错误。示例："
              f"{'、'.join(unmatched[:5])}")

    return merged, f"麦当劳 MCP 实时数据 · {store_name}", stats


def load_replay(nutri_path: str, menu_path: str, store_name: str):
    """从 --dump-raw 保存的原始响应重放，不重新调用 MCP。

    用途：门店菜单随时段变化（早市只有早餐），若每次都重跑线上报告会不断变形。
    用快照重放可以把对外发布的报告锁定在某一次有代表性的拉取，且结果可复现。
    """
    import json

    with open(nutri_path, encoding="utf-8") as f:
        nutri_raw = json.load(f)
    with open(menu_path, encoding="utf-8") as f:
        menu_raw = json.load(f)

    nutri = mcd_parse.parse_nutrition(nutri_raw)
    menu = mcd_parse.parse_menu(menu_raw)
    print(f"[✓] 快照重放：营养 {len(nutri)} 条 / 菜单 {len(menu)} 条")
    if not nutri or not menu:
        raise RuntimeError("快照解析后为空，请确认文件是 --dump-raw / probe 保存的原始 MCP 响应。")

    merged, unmatched, stats = mcd_parse.join_by_name(nutri, menu)
    print(f"[✓] 精确匹配 {stats['matched']} 条"
          f"（套餐/周边排除 {stats['menu_combo_excluded']} 条，未匹配 {stats['unmatched']} 条）")
    if not merged:
        raise RuntimeError("快照数据无法按名称匹配，无法计算性价比。")

    return merged, f"麦当劳 MCP 实时数据快照 · {store_name}", stats


def load_demo():
    print("[!] 未检测到 MCD_MCP_TOKEN，使用内置示例数据（非官方实时数据）")
    return demo_data.load_demo(), "内置示例数据", {}


def main() -> int:
    ap = argparse.ArgumentParser(description="生成麦当劳营养红黑榜报告")
    ap.add_argument("--demo", action="store_true", help="强制使用内置示例数据")
    ap.add_argument("--city", default=DEFAULT_CITY, help="门店搜索城市")
    ap.add_argument("--keyword", default=DEFAULT_KEYWORD, help="门店搜索关键词")
    ap.add_argument("--store-code", help="直接指定门店编码，跳过搜索")
    ap.add_argument("--dump-raw", action="store_true", help="保存 MCP 原始响应")
    ap.add_argument("--replay", nargs=2, metavar=("NUTRI", "MENU"),
                    help="从 data/raw/ 中的原始响应快照重放，不调用 MCP")
    ap.add_argument("--store-name", default="麦当劳南京新百餐厅",
                    help="配合 --replay 使用，写入报告的数据源说明")
    ap.add_argument("--out", default="output/index.html", help="报告输出路径")
    args = ap.parse_args()

    has_token = bool(os.environ.get("MCD_MCP_TOKEN", "").strip())
    use_demo = args.demo or (not has_token and not args.replay)

    try:
        if use_demo:
            items, source, stats = load_demo()
        elif args.replay:
            items, source, stats = load_replay(args.replay[0], args.replay[1], args.store_name)
        else:
            items, source, stats = load_live(
                args.dump_raw, args.city, args.keyword, args.store_code)
    except Exception as e:
        print(f"[x] 获取失败：{type(e).__name__}: {e}")
        print("    可先用 --demo 跑通链路：python run.py --demo")
        return 1

    rankings = rank.build_rankings(items)
    meta = {"count": len(items), "source": source, "demo": use_demo, "stats": stats}
    path = report.write_report(rankings, meta, args.out)

    print(f"\n[✓] 报告已生成：{path}")
    print(f"    样本 {len(items)} 款 · 数据源：{source}")
    if rankings["all"]:
        b = rankings["all"][0]
        print(f"    综合第一：{b['name']}（{b['score']} 分 · 蛋白密度 {b['protein_density']} · "
              f"每元 {b['protein_per_yuan']}g）")
    if use_demo:
        print("\n[i] 当前为示例数据。配置 MCD_MCP_TOKEN 后重跑即切换为真实数据。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
