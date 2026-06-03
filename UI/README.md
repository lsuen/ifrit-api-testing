# ifrit API 自动化测试平台 · Web UI

面向测试/业务同学的**可视化操作台**，与 CLI 完全解耦，通过 `subprocess` 调用 `main.py`。

> 与 [用户详细使用手册.md](../用户详细使用手册.md) 流程一致：冒烟 → AI 生成 → 全局鉴权执行 → 报告查看。

## 功能模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 仪表盘 | `/` | 用例统计、快捷入口、鉴权与环境信息 |
| 执行测试 | `/execute` | 场景预设（冒烟/人工/地址业务流/自定义）、全局鉴权、SSE 日志 |
| AI 实验室 | `/ai` | 一键生成（本地/URL）、`--chat` 交互命令、生成后执行 |
| 报告中心 | `/reports` | `reports/runs/` 列表、生成 HTML、清理 |
| 文件编辑 | `/advanced` | Ace 编辑器，编辑 fixtures / 配置（高级模式） |

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
  root_path: "../"      # 指向 ifrit-apitest 根目录
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

## 鉴权说明

- **冒烟**：默认不需要全局鉴权
- **人工 manual**：CSV 可自带登录，也可勾选「全局鉴权」
- **AI 用例 / 地址业务流**：请勾选「全局鉴权」（账号见 `config/settings/auth.ini`，默认 test/123456）

## AI 能力

- **一键生成**：本地 `api_docs/*.json` 或远程 Swagger / Apifox URL
- **端点过滤**：如 `/api/address`
- **交互模式**：等效 `python main.py --chat -- doc ... endpoint ... generate`

## 架构

```
templates + platform.js
    → Flask API (/api/execute, /api/ai/*, /api/process/*/stream)
    → services/cli_runner.py (subprocess + SSE)
    → ../main.py
```

## 测试

```bash
cd UI
python -m pytest tests/ -v
```

## 版本

- **v2.0** — 专业操作台：仪表盘、执行向导、AI 实验室（含 chat）、报告 runs、高级编辑
- **v1.0** — 仅文件管理器（已重构）

作者：孙文龙
