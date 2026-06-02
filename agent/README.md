# Agent 模块

AI 用例生成、LLM 调用、ReAct 编排与 Skill 注册。

## 目录结构

```
agent/
├── llm/client.py              # OpenAI 兼容 LLM 客户端
├── parser/document_parser.py
├── generator/                 # 用例生成、模板、质量验证
├── pipeline/generator.py      # CLI 入口 AIGenerator（ReAct + Skill）
├── actions/                   # 可组合 Action
│   ├── probe_endpoint.py      # curl/HTTP 端点探测
│   ├── discover_auth.py       # 从 Swagger 重写 auth.ini
│   └── prune_failed_cases.py  # 删除验证失败的 AI 用例行
├── react/loop.py              # ReAct 顺序执行
└── skills/registry.py         # Skill -> Action 列表
```

## 预置 Skill

| Skill | Actions |
|-------|---------|
| `case_generation` | parse → generate → validate → save |
| `parse_only` | parse |
| `generate_and_validate` | parse → generate → validate |
| `auth_discovery` | discover_auth（重写 `config/settings/auth.ini`） |
| `endpoint_probe` | probe_endpoint |
| `ai_quality_loop` | probe → parse → generate → validate → save → prune |

## CLI 示例

```bash
# 从 Swagger 生成 /api/test 用例（输出 fixtures/ai/csv/）
python main.py --ai-generate \
  --input-doc api_docs/apispec_1.json \
  --swagger-endpoint /api/test \
  --output-format csv

# 冒烟测试
python main.py --file fixtures/smoke/csv/api_test_smoke.csv --env environment

# AI 用例 + 全局鉴权
python main.py --file fixtures/ai/csv/ai_xxx.csv --global-auth --suite ai

# 全流程调试
bash debug.sh          # WSL/Linux
debug.bat              # Windows
```

配置：`config/settings/ai.ini`、`config/settings/auth.ini` + `.env`（`OPENAI_API_KEY` 等）。
