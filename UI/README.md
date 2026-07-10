# ifrit API 自动化测试平台 · Web UI

面向测试/业务同学的**可视化操作台**，与 CLI 完全解耦，通过 `subprocess` 调用 `main.py`。

> 与 [用户详细使用手册.md](../用户详细使用手册.md) 流程一致：设置 → 导入/生成 → 执行 → 报告。

## 功能模块（v0.3）

| 模块 | 路径 | 说明 |
|------|------|------|
| 仪表盘 | `/` | 就绪检查、一键流水线（冒烟 / AI / 导入→执行） |
| 设置 | `/settings` | AI / 环境 / 鉴权 / 偏好、连接自检 |
| 导入用例 | `/import` | Postman / CSV / JSON，AI 诊断，保存后自动入库 |
| AI 生成 | `/ai` | 一键生成、交互 `--chat`、RAG、Skill 自动匹配 |
| 执行测试 | `/execute` | 场景预设、全局鉴权、SSE 日志、测试 AI 辅助 |
| 查看报告 | `/reports` | Run 列表、HTML 生成、在线查看 |
| Agent 对话 | `/agent` | 自然语言 → Skill 路由 → CLI 执行 |
| 知识库 | `/knowledge` | RAG 入库、检索、重建 |
| Skill 管理 | `/skills` | 内置 / 外部 Skill 库 |
| 控制台 | `/console` | 安全 CLI/Chat 单行调试 |
| 文件编辑 | `/advanced` | Ace 编辑器（高级） |

## 小白上手路径

```
1. 设置 (/settings) — 填环境、鉴权、AI，跑就绪检查
2. 仪表盘 (/) — 点「冒烟全流程」或「导入→执行」
3. 报告中心 (/reports) — 查看 HTML 报告
```

进阶：Agent 对话说「生成地址用例并执行」；或走导入中心 → AI 实验室 → 执行。

## 快速开始

```bash
cd UI
# Windows
run.bat
# Linux/macOS
chmod +x run.sh && ./run.sh
```

浏览器访问：**http://127.0.0.1:5001**

## 配置

`config.yaml`：

```yaml
ifrit:
  root_path: "../"
  python_bin: "python"
  cli_script: "main.py"
server:
  port: 5001
paths:
  fixtures: "fixtures"
  reports_runs: "reports/runs"
  ...
presets:
  smoke_file: "fixtures/smoke/csv/api_test_smoke.csv"
  ai_business_file: "fixtures/ai/csv/ai_address_business.csv"
```

UI 偏好写入 `.ifrit/ui_prefs.yaml`（RAG 默认开、自动入库等）。

## 鉴权说明

- **冒烟**：可不勾选全局鉴权
- **manual / 导入用例**：建议勾选「全局鉴权」
- **AI 用例**：执行时请开启「全局鉴权」（`config/settings/auth.ini`）

## 架构

```
templates + platform.js / dashboard.js / agent.js
    → Flask API (/api/execute, /api/ai/*, /api/agent/plan, /api/settings/*)
    → services/cli_runner.py (subprocess + SSE)
    → ../main.py → agent/skills → ReAct Actions
```

## 测试

```bash
cd ..
py -3.10 -m unittest UI.tests.test_app UI.tests.test_agent_dialog -v
```

## 版本

- **v0.3** — 设置中心、仪表盘流水线、Agent 对话、知识库 RAG 串联、侧栏新手路径
- **v2.0** — 专业操作台：执行向导、AI 实验室、报告 runs
- **v1.0** — 仅文件管理器（已重构）

作者：孙文龙
