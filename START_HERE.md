# 麦当劳程序员创意开发大赛 · 参赛项目

**项目：麦当劳营养红黑榜 · 蛋白质性价比计算器**

> 官方给你热量，菜单给你价格。没人告诉你：你花的每一块钱，到底买到了多少克蛋白质。

---

## 当前状态：已接入真实 MCP 数据 ✅

最新一次运行（麦当劳南京新百餐厅，storeCode `1990346`）：

```
营养 160 条 / 菜单 124 条 → 精确匹配 20 款
综合第一：薄皮焦香V翅（85.4 分 · 蛋白密度 8.85 · 每元 1.097g）
```

`output/index.html` 当前就是**真实数据生成的报告**。

### 重新生成

```bash
export MCD_MCP_TOKEN="你的_Token"
python run.py                          # 默认 南京 / 麦当劳
python run.py --city 上海 --keyword 麦当劳
python run.py --store-code 1990346
```

没 Token 时 `python run.py --demo` 仍可用内置示例数据预览。

---

## 模块清单

| 模块 | 状态 | 说明 |
|---|---|---|
| MCP 客户端 | ✅ 完成 | `src/mcd_client.py`，Streamable HTTP + SSE 解包 |
| 响应解析 | ✅ 完成 | `src/mcd_parse.py`，解 Markdown 包裹 + 自定义表格 + 双向唯一匹配 |
| 指标引擎 | ✅ 完成 | `src/rank.py`，四项指标 + 综合评分，真实数据已手工复核 |
| 报告生成器 | ✅ 完成 | `src/report.py`，自包含 HTML（33.5KB，零外部依赖） |
| 示例数据 | ✅ 完成 | `src/demo_data.py`，27 款餐品 |
| CLI 入口 | ✅ 完成 | `run.py`，自动检测 Token 切换真实/示例数据 |
| SKILL.md | ✅ 完成 | WorkBuddy 加载入口 |
| 官方 5 项必需文件 | ✅ 齐备 | 见下表 |

### 官方必需文件核对

| 文件 | 状态 |
|---|---|
| `README.md` | ✅ 项目介绍 / 安装 / 使用示例 / 目标用户 |
| `CONTEST_DECLARATION.md` | ✅ **官方原文未改动**，MD5 `91a7b32ec28098b609ca3f215cdf7147` |
| `MCP_INTEGRATION.md` | ✅ 真实 Tool 清单 + 流程 + 业务价值 |
| `mcp-config.example.json` | ✅ 仅 `${MCD_MCP_TOKEN}` 占位 |
| `workbuddy.md` | ✅ 已记录四轮开发对话 |

---

## 立即体验（不需要 Token）

```bash
cd mcd-1024-skill
python run.py --demo
# 打开 output/index.html
```

## 切换真实数据（3 步）

### 1. 申请 Token

https://open.mcd.cn/mcp → 手机号登录 → 控制台 → 激活 → 复制 Token

### 2. 跑通

```bash
export MCD_MCP_TOKEN="你的_Token"      # PowerShell: $env:MCD_MCP_TOKEN="..."
python run.py --dump-raw               # 同时保存原始响应用到 data/raw/
```

### 3. 校准字段（重要）

服务端返回的字段名可能与预期不同。`--dump-raw` 之后：

1. 打开 `data/raw/` 里最新的 `nutrition_*.json` 和 `menu_*.json`
2. 看真实字段名
3. 若对不上，在 `src/rank.py` 的 `FIELD_CANDIDATES` 里补上

程序会在数据合并为空时给出明确提示，不会静默产出错误结果。

---

## 上传 GitHub ✅ 已完成

仓库：https://github.com/york0307/mcd-protein-value （Public）

```bash
git init && git add -A && git commit -m "..."
git branch -M main
git remote add origin https://github.com/york0307/mcd-protein-value.git
git push -u origin main
```

⚠️ push 前先跑安全自查（见 `docs/checklist.md` 第三节）：

```bash
grep -rInE "(Bearer [A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9]{20,}|token[\"'=: ]+[A-Za-z0-9_-]{16,})" . --exclude-dir=.git
```

> 注：本机 `gh` CLI 不可用（`universal-user-agent` 调 powershell 报 `spawnSync EBUSY`），
> 且无 SSH 密钥 → 走 HTTPS + PAT。PAT 不要写进 remote URL，用一次性 URL 推完即弃。

### 更新在线报告（gh-pages 孤儿分支）

Pages 从 `gh-pages` 分支根目录发布（GitHub 的 legacy 模式只允许 `/` 或 `/docs`，不支持 `/output`）。
重新生成报告后同步：

```bash
cp output/index.html ./index.html && touch .nojekyll
git checkout --orphan gh-pages
git rm -rf --cached . 
git add index.html .nojekyll
git commit -m "docs: 更新报告"
git push -f origin gh-pages
git checkout -f main && rm -f index.html .nojekyll
```

线上地址：https://york0307.github.io/mcd-protein-value/

---

## 报名

到 https://github.com/M-China/mcd-developer-innovation-challenge/issues
按 `docs/issue-template.txt` 格式发布 Issue：

```
【参赛申请】
项目名称：麦当劳营养红黑榜 · 蛋白质性价比计算器
项目地址：https://github.com/york0307/mcd-protein-value
项目简介：把麦当劳的营养数据和价格 join 起来，算出每一块钱能买到多少克蛋白质。
```

---

## 传播建议

这个项目的 Star 增长点在于**报告本身可以被转发**：

1. 在线报告已上线：https://york0307.github.io/mcd-protein-value/
2. 截图「三个反直觉发现」+「红黑榜」发小红书 / 即刻 / V2EX
3. README 首屏的结论表格本身就是可传播内容

**不需要 Token 就能看报告**是这个项目最大的传播优势，务必用上。

---

## 时间提醒

| 事项 | 截止 |
|---|---|
| 报名 + Star 累积 | **2026-10-25 23:59** |
| 定榜 | 2026-10-26 00:00 |
| 奖品兑换信息提交 | 2026-11-14 |
