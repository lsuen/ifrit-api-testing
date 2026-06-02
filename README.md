# ifrit API自动化测试框架

一个功能强大、灵活易用的API自动化测试框架，支持数据驱动、AI智能生成测试用例等功能。

## 目录结构

```
ifrit/
├── config/                  # 配置模块
│   ├── loader.py            # 统一加载 .env + settings/*.ini
│   ├── config.py            # 被测 API / 测试数据配置
│   ├── ai_config.py         # LLM / AI 生成配置
│   └── settings/            # 可提交的团队默认配置
│       ├── app.ini
│       ├── env_config.ini
│       ├── test_data.ini
│       ├── column_mapping.ini
│       └── ai.ini
├── agent/                   # AI Agent（ReAct/Action/Skill，规划中）
│   ├── __init__.py
│   ├── request_handler.py   # 请求处理工具
│   ├── assert_handler.py    # 断言工具
│   ├── data_handler.py      # 数据处理器(含关联和正则)
│   ├── test_executor.py     # 测试执行器（统一执行逻辑）
│   ├── ai_client.py         # AI客户端
│   ├── document_parser.py   # 文档解析器
│   ├── case_generator.py    # 测试用例生成器
│   ├── template_engine.py   # 模板引擎
│   ├── quality_validator.py # 质量验证器
│   ├── cli_manager.py       # 命令行界面管理器
│   ├── report_manager.py    # 报告管理器
│   └── test_runner.py       # 测试运行器
├── utils/                   # 工具类目录
│   ├── __init__.py
│   ├── logger.py            # 日志工具
│   ├── common_utils.py      # 通用工具
│   └── test_case_reader.py  # 测试用例读取器
├── drivers/                 # 测试驱动目录
│   ├── __init__.py
│   ├── conftest.py          # Pytest配置和fixture
│   ├── test_api_excel_driver.py  # Excel测试驱动
│   ├── test_api_csv_driver.py    # CSV测试驱动
│   ├── test_api_json_driver.py   # JSON测试驱动
│   └── test_all_drivers.py       # 统一测试驱动
├── fixtures/                # 测试用例数据（人工 / AI / 冒烟 分离）
│   ├── manual/              # 人工编写用例
│   │   ├── csv/
│   │   ├── json/
│   │   └── excel/
│   ├── ai/                  # AI 生成用例（可 prune）
│   │   └── csv/
│   └── smoke/               # curl 验证过的冒烟用例
│       └── csv/
├── core/
│   └── auth_manager.py      # 全局鉴权（与用例内 login 解耦）
├── scripts/
│   └── debug_workflow.py    # 全流程调试脚本
├── debug.sh                 # Linux/WSL 调试入口
├── debug.bat                # Windows 调试入口
├── __docs/                      # 文档目录
│   ├── AI_GUIDE.md                  # AI功能使用指南
│   ├── command_reference.md         # 命令行参考
│   ├── ifrit使用手册.md             # 使用手册（含Allure部署指南）
│   ├── ifrit命令手册.md             # 命令手册
│   ├── ifrit-二次开发详细手册.md    # 二次开发手册
│   ├── ifrit-yaml数据驱动手册.md    # YAML数据驱动手册
│   └── ifrit-数据库数据驱动.md      # 数据库数据驱动手册
├── __internal_tests/        # 内部单元测试目录（历史）
├── tests/                   # 单元测试目录（新增测试优先放此）
├── build/                   # 构建产物目录
├── .cursor/skills/          # Cursor Agent 项目技能（含开发规范）
├── logs/                    # 日志目录（daily/、errors/，默认不写 api_automation.log）
├── reports/                 # 测试报告（runs/YYYYMMDD_HHMMSS/ + latest.txt）
├── main.py                  # 主程序入口
├── ai_case_generator.py     # AI测试用例生成器独立脚本
├── curltocase_client.py     # Curl转测试用例工具客户端
├── pytest.ini               # Pytest配置文件
└── requirements.txt         # 依赖包列表
```

## 功能特性

1. **数据驱动测试**：支持Excel、CSV、JSON和YAML格式测试用例
2. **AI智能生成**：从接口文档自动生成全面的测试用例
3. **数据关联**：支持接口间数据传递和变量提取
4. **正则表达式支持**：可使用正则表达式提取数据
5. **配置分离**：环境配置与测试数据配置分离
6. **日志记录**：完整的请求/响应日志记录
7. **Allure报告**：生成美观的测试报告，包含curl命令便于问题复现，使用case_name作为测试项标识
8. **多环境支持**：支持多个测试环境配置切换
9. **可扩展架构**：模块化设计，易于扩展
10. **多值变量提取**：支持一次提取多个变量并分别存储
11. **文档解析**：支持Markdown和Swagger格式的接口文档
12. **质量验证**：自动验证生成的测试用例质量并提供修复建议
13. **数据库支持**：支持从数据库读取测试数据
14. **YAML格式支持**：支持YAML格式的测试数据定义

## 安装依赖

```
pip install -r requirements.txt
```

## 快速开始

### 1. 从API文档生成测试用例

```
# 从 Swagger 生成 CSV（输出到 fixtures/ai/csv/）
python main.py --ai-generate --input-doc api_docs/apispec_1.json --swagger-endpoint /api/test --output-format csv

# 指定输出目录
python main.py --ai-generate --input-doc api_docs/apispec_1.json --output-format csv --output-dir fixtures/ai/csv
```

### 2. 执行测试用例

```
# 运行人工 CSV 用例（默认 manual 套件）
python main.py --type csv

# 运行冒烟用例
python main.py --file fixtures/smoke/csv/api_test_smoke.csv

# 运行 AI 生成用例（建议加 --global-auth）
python main.py --file fixtures/ai/csv/ai_xxx.csv --global-auth --suite ai

# 运行指定环境的测试
python main.py --env environment

# 全流程调试（probe → auth → 生成 → 验证 → prune）
debug.bat
# 或 WSL/Linux: bash debug.sh
```

## 简单使用教程

### 1. 基础测试执行
要运行一个简单的测试，首先需要准备测试数据。框架支持多种格式的数据源，最简单的方式是使用Excel或CSV文件定义测试用例。

### 2. 环境配置
修改 `config/settings/env_config.ini` 中对应环境的 `base_url`。

### 3. 运行测试
使用如下命令运行测试：
```
python main.py --type csv
```

### 4. 查看报告
每次运行写入 `reports/runs/<时间戳>/allure-results`，HTML 报告在同 run 的 `html/` 下；最新 run 见 `reports/latest.txt`。

测试完成后，可以通过以下命令启动报告服务器：
```
python main.py --serve-report
```

清理过期产物（保留策略见 `config/settings/app.ini` `[retention]`）：
```
python main.py --clean logs --dry-run
python main.py --clean reports
python main.py --clean all --keep-days 7
```

> **详细使用方法请查看** [__docs/ifrit使用手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit使用手册.md)

## 简单二次开发教程

### 1. 添加新的数据格式支持
要添加新的数据格式支持，你需要：
1. 在 [core/](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core) 目录下创建相应的解析器
2. 在 [drivers/](file:///C:/CodeFiles/PyProjects/ifrit-apitest/drivers) 目录下创建对应的测试驱动文件
3. 修改 [core/cli_manager.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/cli_manager.py) 添加新的格式选项

### 2. 扩展断言功能
可以通过修改 [core/assert_handler.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/assert_handler.py) 文件来添加新的断言类型。

> **详细开发方法请查看** [__docs/ifrit-二次开发详细手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-二次开发详细手册.md)

## 简单数据驱动增加教程

### 1. 添加YAML格式支持
框架已经内置了YAML格式的支持，只需在测试数据文件中使用 `.yaml` 或 `.yml` 扩展名即可。

### 2. 添加数据库支持
框架支持从数据库读取测试数据，需要：
1. 配置数据库 host/port 到 `config/settings/env_config.ini`，账号密码写入 `.env`（`DB_USER` / `DB_PASSWORD`）
2. 编写数据库查询语句来获取测试数据

> **YAML数据驱动详细方法请查看** [__docs/ifrit-yaml数据驱动手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-yaml数据驱动手册.md)

> **数据库数据驱动详细方法请查看** [__docs/ifrit-数据库数据驱动.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-数据库数据驱动.md)

## AI功能详细说明

框架集成了强大的AI测试用例生成功能，支持：

- **文档格式**：Markdown、Swagger JSON/YAML
- **生成类型**：正向、反向、边界、结构、路径、权限测试用例
- **输出格式**：Excel、CSV、JSON
- **质量保证**：自动质量验证和修复建议
- **批量处理**：支持多文档批量生成
- **在线文档**：支持在线Swagger文档解析

详细使用方法请参考 [__docs/AI_GUIDE.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/AI_GUIDE.md)。

## 命令行参考

详细命令行参数说明请参考 [__docs/ifrit命令手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit命令手册.md)。

## 运行内部单元测试

框架包含全面的内部单元测试，确保各组件稳定可靠：

```
# 运行所有内部单元测试
python -m unittest discover __internal_tests/

# 运行特定的内部单元测试
python __internal_tests/test_engines.py
python __internal_tests/test_parsers.py
python __internal_tests/test_utils.py
python __internal_tests/test_business_logic.py
```

## 注意事项

1. **环境配置**：确保 `config/settings/env_config.ini` 中 API 地址正确；个人临时 override 可用 `.env` 的 `IFRIT_BASE_URL`
2. **依赖安装**：运行前请确保已安装所有依赖包
3. **Allure报告**：如需使用报告功能，需要安装Allure命令行工具
4. **权限问题**：确保框架有权限读取测试数据文件和写入报告目录
5. **AI功能**：使用AI生成功能需要有效的API密钥和网络连接
6. **数据安全**：不要在配置文件中存储敏感信息，如API密钥、数据库密码等
7. **性能考虑**：运行大量测试用例时，请确保系统有足够的内存和存储空间

## 其他资源

- [__docs/ifrit使用手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit使用手册.md) - 详细的使用说明
- [__docs/ifrit命令手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit命令手册.md) - 完整的命令参数说明
- [__docs/ifrit-二次开发详细手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-二次开发详细手册.md) - 二次开发指导
- [__docs/ifrit-yaml数据驱动手册.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-yaml数据驱动手册.md) - YAML数据驱动使用说明
- [__docs/ifrit-数据库数据驱动.md](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__docs/ifrit-数据库数据驱动.md) - 数据库数据驱动使用说明

## 开发规范

本项目采用永久执行规范，详见 [`.cursor/skills/ifrit-project-dev/SKILL.md`](.cursor/skills/ifrit-project-dev/SKILL.md)。

### 任务闭环流程

1. 读取/更新 `.MemoryForAI/` 项目记忆
2. 按代码规范完成开发（中文注释、语义化命名、参数校验等）
3. 编写并运行单元测试（`tests/` 或 `__internal_tests/`）
4. Git 提交（`feat` / `fix` / `refactor` / `doc`，中文描述）
5. 推送钉钉迭代通知（见下方）
6. 同步更新 README 与项目记忆

### 目录约束

| 目录 | 用途 |
|------|------|
| `tests/` | 单元测试、测试脚本、测试配置 |
| `build/` | 打包产物、编译文件、部署包 |
| `core/` | 核心业务逻辑 |
| `utils/` | 工具类 |
| `config/` | 配置文件 |
| `drivers/` | 测试驱动 |
| `__docs/` | 项目文档 |
| `__internal_tests/` | 历史内部单元测试 |

### 配置分层

| 类型 | 位置 | 示例 |
|------|------|------|
| 敏感 / 个人 | `.env`（gitignore） | `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`DINGTALK_ACCESS_TOKEN` |
| 团队稳定 | `config/settings/*.ini` | 测试环境 URL、LLM endpoint、列映射 |

首次使用：`cp .env.example .env` 并填写本地密钥。

### Git Hooks（钉钉 post-commit）

```bash
git config core.hooksPath .githooks
```

此后每次 `git commit` 会自动调用钉钉通知脚本（需 `.env` 配置 `DINGTALK_ACCESS_TOKEN`）。

### CI

GitHub Actions 见 `.github/workflows/ci.yml`：PR 跑单元测试；smoke 需配置仓库 Secret `IFRIT_BASE_URL`。

### 钉钉迭代通知

commit 后发送（需 `.env` 中配置 `DINGTALK_ACCESS_TOKEN`）：

```bash
python .cursor/skills/ifrit-project-dev/scripts/send_dingtalk_notify.py \
  --commit-type feat \
  --commit-hash <提交哈希> \
  --summary "本次修改说明" \
  --modules "core/, tests/" \
  --reason "改动原因"
```

预览报告不发送：追加 `--dry-run`。

### _legacy 说明

早期 README 中的 `testcases`、`docs`、`internal_tests` 等路径已统一为当前目录结构，请以本节为准。

## 贡献

欢迎提交Issue和Pull Request来改进框架。

## 许可证

[MIT License](LICENSE)
