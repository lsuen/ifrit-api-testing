# 测试用例数据目录（fixtures）

人工用例与 AI 用例分离，禁止混放。

| 目录 | 用途 |
|------|------|
| `manual/csv` | **主格式**：人工编写、Review 过的用例（推荐） |
| `manual/json` `manual/excel` | 历史镜像，与 CSV 内容重复，逐步弃用 |
| `ai/csv` | AI 生成用例（可 prune 删除失败项） |
| `smoke/csv` | 已验证的冒烟用例，CI / 日常健康检查 |

## 套件（`--suite`）

| 值 | 扫描范围 |
|----|----------|
| `manual` | 默认，仅 `fixtures/manual/` |
| `smoke` | `fixtures/smoke/csv/` |
| `ai` | `fixtures/ai/csv/` |
| `all` | manual + ai + smoke |

## 暂挂用例

与现网 API 行为不一致的 manual 用例已设 `enabled=0`，待按 Swagger 校准后再启用。
