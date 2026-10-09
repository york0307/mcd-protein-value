#!/usr/bin/env python3
"""
麦当劳 MCP 连通性自检脚本

用途：验证 MCD_MCP_TOKEN 是否可用、MCP Server 是否可达，并列出服务端实际暴露的全部 Tool。
这是搭建阶段的第一步 —— 确认能连上，再开始写业务逻辑。

用法：
    export MCD_MCP_TOKEN="你的_Token"        # Windows PowerShell: $env:MCD_MCP_TOKEN="..."
    python scripts/check_mcp.py
"""

import json
import os
import sys
import urllib.error
import urllib.request

MCP_URL = "https://mcp.mcd.cn"


def rpc(token: str, method: str, params: dict | None = None, req_id: int = 1) -> dict:
    """发一次 JSON-RPC 请求。同时带上 Accept，兼容 Streamable HTTP。"""
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        body["params"] = params

    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")

    # 服务端可能以 SSE 形式返回：抽取 data: 行后再解析
    if raw.lstrip().startswith("event:") or "data:" in raw[:64]:
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                break
    return json.loads(raw)


def main() -> int:
    token = os.environ.get("MCD_MCP_TOKEN", "").strip()
    if not token:
        print("[x] 未检测到环境变量 MCD_MCP_TOKEN")
        print("    请先执行：export MCD_MCP_TOKEN=\"你的_Token\"")
        print("    Token 申请：https://open.mcd.cn/mcp")
        return 1

    print(f"[*] 目标服务：{MCP_URL}")
    print(f"[*] Token 前缀：{token[:6]}...（长度 {len(token)}）\n")

    try:
        init = rpc(token, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "mcd-1024-check", "version": "1.0.0"},
        })
    except urllib.error.HTTPError as e:
        print(f"[x] HTTP {e.code}: {e.reason}")
        if e.code == 401:
            print("    → Token 无效或已过期，请到 open.mcd.cn/mcp 重新激活")
        elif e.code == 429:
            print("    → 触发限流（600 次/分钟），稍后重试")
        return 1
    except Exception as e:
        print(f"[x] 连接失败：{type(e).__name__}: {e}")
        return 1

    if "error" in init:
        print(f"[x] 初始化被拒绝：{json.dumps(init['error'], ensure_ascii=False)}")
        return 1

    server = init.get("result", {}).get("serverInfo", {})
    print(f"[✓] 握手成功：{server.get('name', '?')} v{server.get('version', '?')}\n")

    try:
        listed = rpc(token, "tools/list", req_id=2)
    except Exception as e:
        print(f"[x] 拉取工具列表失败：{e}")
        return 1

    tools = listed.get("result", {}).get("tools", [])
    if not tools:
        print("[!] 未返回任何 Tool")
        return 1

    print(f"[✓] 可用 Tool 共 {len(tools)} 个：\n")
    for i, t in enumerate(tools, 1):
        name = t.get("name", "?")
        desc = (t.get("description") or "").replace("\n", " ").strip()
        if len(desc) > 56:
            desc = desc[:56] + "…"
        print(f"  {i:2d}. {name:<28} {desc}")

    print("\n[✓] 环境就绪，可以开始开发。")
    print("    提示：把上面这份 Tool 清单回填到 MCP_INTEGRATION.md 的表格中。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
