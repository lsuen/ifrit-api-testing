# 历史文档目录

> **注意：** 部分文档仍引用旧路径 `data/`、`testcases/`，请以根目录 [README.md](../README.md) 与 [fixtures/README.md](../fixtures/README.md) 为准。

## 推荐入口（按读者）

| 读者 | 文档 |
|------|------|
| **测试 / 业务同学（无编程基础）** | **[用户详细使用手册.md](../用户详细使用手册.md)** |
| 研发 / 快速上手 | [README.md](../README.md) |
| AI 与 Agent | [agent/README.md](../agent/README.md) · [AI_GUIDE.md](AI_GUIDE.md) |
| 命令参数全集 | [ifrit命令手册.md](ifrit命令手册.md) |
| 用例数据 | [fixtures/README.md](../fixtures/README.md) |

## 当前约定

| 旧路径 | 新路径 |
|--------|--------|
| `data/csv_data/` | `fixtures/manual/csv/` 或 `fixtures/ai/csv/` |
| `data/ai_generated/` | `fixtures/ai/csv/` |
| `testcases/` | `drivers/` |

## 鉴权速记

- **manual 用例**：可在 CSV 内写登录步骤 + `{{token}}`，或加 `--global-auth` 使用 `config/settings/auth.ini`
- **AI 用例**：执行时**必须** `--global-auth`（默认账号 test/123456）

详见 [用户详细使用手册.md 第 4 节](../用户详细使用手册.md#4-鉴权说明手工用例-vs-ai-用例)。
