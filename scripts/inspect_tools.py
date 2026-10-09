#!/usr/bin/env python3
"""开发辅助：导出 MCP 服务端全部 Tool 的 inputSchema，用于确认必填参数。

    python scripts/inspect_tools.py            # 列出全部工具名
    python scripts/inspect_tools.py query-meals   # 看某个工具的完整 schema
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from mcd_client import McpClient, dump_raw  # noqa: E402


def main() -> int:
    client = McpClient()
    client.initialize()
    tools = client.list_tools()
    path = dump_raw(tools, "tools")
    print(f"[✓] 共 {len(tools)} 个 Tool，已保存 {path}\n")

    wanted = sys.argv[1:] 
    for t in tools:
        name = t.get("name", "?")
        schema = t.get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = schema.get("required") or []

        if wanted and name not in wanted:
            continue

        if not wanted:
            req = ",".join(required) if required else "-"
            print(f"  {name:<30} 必填: {req}")
            continue

        print(f"=== {name} ===")
        print(f"描述: {(t.get('description') or '').strip()[:200]}")
        print(f"必填: {required or '无'}")
        if props:
            print("参数:")
            for k, v in props.items():
                mark = "*" if k in required else " "
                print(f"  {mark} {k:<22} {v.get('type','?'):<8} {(v.get('description') or '')[:70]}")
        else:
            print("参数: 无（无需入参）")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
