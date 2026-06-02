# Agent 模块（规划中）

本目录用于将 AI Agent 能力从 `core/` 解耦，后续支持：

- **ReAct**：推理 + 行动循环
- **Action**：可注册、可组合的工具动作
- **Function Calling**：OpenAI 兼容 tools / functions 协议
- **Skill**：与 `.cursor/skills/` 及项目内 skill 注册机制对接

## 当前状态

- LLM 客户端暂仍在 `core/ai_client.py`（用例生成）
- 配置统一由 `config/ai_config.py` + `config/settings/ai.ini` + `.env` 提供
- 新 Agent 代码请放入本目录，避免继续膨胀 `core/`

## 规划结构

```
agent/
├── actions/      # 原子动作（HTTP、解析、写文件等）
├── react/        # ReAct 循环与状态机
├── skills/       # Skill 注册与加载
└── llm/          # （后续）从 core 迁入的 LLM 客户端封装
```

## 配置约定

| 类型 | 位置 |
|------|------|
| LLM endpoint / model / prompt | `config/settings/ai.ini` |
| API Key / 个人 base_url、model override | `.env` |
| 被测 API 环境 | `config/settings/env_config.ini` |

Agent 模块应通过 `from config import AIConfig` 获取 LLM 配置，不直接读 ini。
