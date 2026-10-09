#!/usr/bin/env python3
"""开发辅助：实际调用几个 Tool 并把原始响应落盘，用于确认结构。

    python scripts/probe.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from mcd_client import McpClient, dump_raw  # noqa: E402


def brief(obj, n: int = 900) -> str:
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)
    return s[:n]


def main() -> int:
    c = McpClient()
    c.initialize()

    print("=== 1) query-nearby-stores (beType=1, searchType=1) ===")
    try:
        r = c.call_tool("query-nearby-stores", {"beType": 1, "searchType": 1})
        print(brief(r, 1200))
        dump_raw(r, "probe_stores")
    except Exception as e:
        print("失败:", e)

    print("\n=== 2) delivery-query-addresses ===")
    try:
        r = c.call_tool("delivery-query-addresses")
        print(brief(r, 900))
        dump_raw(r, "probe_addresses")
    except Exception as e:
        print("失败:", e)

    return 0


if __name__ == "__main__":
    sys.exit(main())
