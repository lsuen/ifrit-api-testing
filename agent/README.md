# Agent 模块

AI 用例生成、LLM 调用、ReAct 编排与 Skill 注册。

## 目录结构

```
agent/
├── llm/client.py           # OpenAI 兼容 LLM 客户端
├── parser/document_parser.py
├── generator/              # 用例生成、模板、质量验证
├── pipeline/generator.py   # CLI 入口 AIGenerator（ReAct + Skill）
├── actions/                # 可组合 Action
├── react/loop.py           # ReAct 顺序执行
└── skills/registry.py      # Skill -> Action 列表
```

## 预置 Skill

| Skill | Actions |
|-------|---------|
| `case_generation` | parse → generate → validate → save |
| `parse_only` | parse |
| `generate_and_validate` | parse → generate → validate |

## CLI 示例

```bash
# 从 Swagger 生成 /api/test 用例
python main.py --ai-generate \
  --input-doc api_docs/apispec_1.json \
  --swagger-endpoint /api/test \
  --output-format csv \
  --output-dir data/csv_data

# 执行 smoke 用例（与 Swagger 响应一致）
python main.py --type csv \
  --file data/csv_data/api_test_smoke.csv \
  --env environment
```

配置：`config/settings/ai.ini` + `.env`（`OPENAI_API_KEY` 等）。
