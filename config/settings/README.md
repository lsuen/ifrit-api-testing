# 配置文件说明（可提交 Git）

| 文件 | 用途 |
|------|------|
| `app.ini` | 日志等行为配置 |
| `env_config.ini` | 被测 API 多环境 URL、数据库 host/port |
| `test_data.ini` | 测试数据目录 |
| `column_mapping.ini` | Excel/CSV/JSON 列名映射 |
| `ai.ini` | LLM endpoint、模型、生成策略、prompt（不含密钥） |

敏感项（API Key、钉钉 token、DB 密码）请写入项目根目录 `.env`，参考 `.env.example`。
