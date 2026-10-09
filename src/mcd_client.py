#!/usr/bin/env python3
"""麦当劳 MCP 客户端 —— Streamable HTTP / JSON-RPC 2.0

只做三件事：握手、列工具、调工具。
服务端可能以 SSE 形式返回，故统一做了 SSE 解包。

设计原则：
- 不在本模块内做任何业务假设，原始响应原样返回给上层；
- 拉取后可 dump 到 data/raw/，便于校准字段映射（服务端 schema 可能演进）。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any

MCP_URL = "https://mcp.mcd.cn"
PROTOCOL_VERSION = "2025-06-18"
CST = timezone(timedelta(hours=8))


class McpError(RuntimeError):
    """MCP 调用失败。"""


class McpClient:
    def __init__(self, token: str | None = None, url: str = MCP_URL, timeout: int = 30):
        self.token = token or os.environ.get("MCD_MCP_TOKEN", "").strip()
        self.url = url
        self.timeout = timeout
        self._seq = 0
        if not self.token:
            raise McpError("缺少 MCP Token，请设置环境变量 MCD_MCP_TOKEN")

    # ---------- 底层 ----------

    def _post(self, payload: dict) -> dict:
        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            hint = {
                401: "Token 无效或已过期，请到 open.mcd.cn/mcp 重新激活",
                403: "Token 无权限调用该工具",
                429: "触发限流（600 次/分钟），请稍后重试",
            }.get(e.code, "")
            raise McpError(f"HTTP {e.code} {e.reason}" + (f" —— {hint}" if hint else ""))
        except urllib.error.URLError as e:
            raise McpError(f"网络不可达：{e.reason}")
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> dict:
        """兼容纯 JSON 与 SSE（data: 行）两种返回形态。"""
        raw = raw.strip()
        if not raw:
            raise McpError("空响应")
        if raw.startswith("{") or raw.startswith("["):
            return json.loads(raw)
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                body = line[5:].strip()
                if body and body != "[DONE]":
                    return json.loads(body)
        raise McpError(f"无法解析响应：{raw[:200]}")

    def _rpc(self, method: str, params: dict | None = None, req_id: int | None = None) -> dict:
        if req_id is None:
            self._seq += 1
            req_id = self._seq
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params
        resp = self._post(payload)
        if "error" in resp:
            err = resp["error"]
            raise McpError(f"{method} 失败 [{err.get('code')}]: {err.get('message')}")
        return resp

    # ---------- 对外 ----------

    def initialize(self) -> dict:
        return self._rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "mcd-protein-value", "version": "1.0.0"},
        }, req_id=1).get("result", {})

    def list_tools(self) -> list[dict]:
        return self._rpc("tools/list", req_id=2).get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """调用工具并返回 result。文本内容会被归一化为 Python 对象。"""
        result = self._rpc("tools/call", {
            "name": name,
            "arguments": arguments or {},
        }).get("result", {})
        return self._unwrap(result)

    @staticmethod
    def _unwrap(result: Any) -> Any:
        """把 MCP content[] 归一化：优先解出内嵌 JSON，否则返回文本。"""
        if isinstance(result, dict) and "content" in result:
            parts = []
            for item in result.get("content", []):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            text = "\n".join(parts).strip()
            if not text:
                return result
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return result

    # ---------- 便利：抓取本项目所需的两份数据 ----------

    def fetch_nutrition(self) -> Any:
        """餐品营养信息列表（无需入参）。"""
        return self.call_tool("list-nutrition-foods")

    def fetch_menu(self, store_code: str) -> Any:
        """指定门店的可售卖餐品列表（含价格）。

        query-meals 的必填参数为 storeCode / orderType / beType：
          orderType: 1-到店（含到店自取+得来速），2-外送
          beType:    1-到店取餐，2-麦乐送到家，5-得来速，6-企业团餐
        本项目默认取「到店取餐」场景，价格即单品柜台价。
        """
        return self.call_tool("query-meals", {
            "storeCode": store_code,
            "orderType": 1,
            "beType": 1,
        })


def dump_raw(obj: Any, name: str, out_dir: str = "data/raw") -> str:
    """把原始响应落盘，供字段映射校准用。"""
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{name}_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


def find_records(obj: Any) -> list[dict]:
    """从任意嵌套结构里捞出第一组「像列表的记录」。

    服务端返回的层级不确定（可能是 list / {"data": [...]} / {"result": {...}}），
    这里做一次保守的深挖，避免把字段名写死。
    """
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for key in ("data", "list", "items", "records", "foods", "meals", "result", "content"):
            val = obj.get(key)
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return val
            if isinstance(val, dict):
                nested = find_records(val)
                if nested:
                    return nested
        for val in obj.values():
            nested = find_records(val)
            if nested:
                return nested
    return []


def pick(d: dict, *candidates: str) -> Any:
    """按候选字段名依次取值，兼容命名差异。"""
    for key in candidates:
        if key in d and d[key] not in (None, ""):
            return d[key]
    low = {str(k).lower(): k for k in d}
    for key in candidates:
        real = low.get(key.lower())
        if real is not None and d[real] not in (None, ""):
            return d[real]
    return None
