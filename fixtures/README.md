# 测试用例数据目录（fixtures）

人工用例与 AI 用例分离，禁止混放。

| 目录 | 用途 |
|------|------|
| `manual/csv` `manual/json` `manual/excel` | 人工编写、Review 过的用例 |
| `ai/csv` `ai/json` | AI 生成用例（可 prune 删除失败项） |
| `smoke/csv` | 已 curl 验证的冒烟用例 |

默认业务测试只加载 `manual/`，AI 用例通过 `--suite ai` 或 debug 脚本执行。
