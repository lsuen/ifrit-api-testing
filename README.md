# API自动化测试框架

一个功能强大、灵活易用的API自动化测试框架，支持数据驱动、AI智能生成测试用例等功能。

## 目录结构

```
api_automation_framework/
├── config/                  # 配置文件目录
│   ├── __init__.py
│   ├── config.py            # 全局配置
│   ├── env_config.ini       # 环境配置
│   ├── test_data_config.ini # 测试数据配置
│   ├── ai_config.py         # AI配置管理
│   └── ai_config.ini        # AI配置文件
├── core/                    # 核心功能目录
│   ├── __init__.py
│   ├── request_handler.py   # 请求处理工具
│   ├── assert_handler.py    # 断言工具
│   ├── data_handler.py      # 数据处理器(含关联和正则)
│   ├── test_executor.py     # 测试执行器（统一执行逻辑）
│   ├── ai_client.py         # AI客户端
│   ├── document_parser.py   # 文档解析器
│   ├── case_generator.py    # 测试用例生成器
│   ├── template_engine.py   # 模板引擎
│   └── quality_validator.py # 质量验证器
├── utils/                   # 工具类目录
│   ├── __init__.py
│   ├── logger.py            # 日志工具
│   └── common_utils.py      # 通用工具
├── testcases/               # 测试用例目录
│   ├── __init__.py
│   ├── conftest.py          # Pytest配置和fixture
│   ├── test_api_excel_driver.py  # Excel测试驱动
│   └── test_api_csv_driver.py    # CSV测试驱动
├── data/                    # 测试数据目录
│   ├── ai_generated/        # AI生成的测试用例
│   └── examples/            # 示例文档
├── docs/                    # 文档目录
│   ├── AI_GUIDE.md          # AI功能使用指南
│   └── command_reference.md # 命令行参考
├── internal_tests/          # 自身单元测试目录
├── logs/                    # 日志目录
├── reports/                 # 测试报告目录
├── main.py                  # 主程序入口
├── ai_case_generator.py     # AI测试用例生成器独立脚本
└── pytest.ini               # Pytest配置文件
```

## 功能特性

1. **数据驱动测试**：支持Excel和CSV格式测试用例
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

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 从API文档生成测试用例

```bash
# 从Markdown文档生成CSV格式测试用例
python main.py --ai-generate --input-doc data/examples/sample_api.md --output-format csv

# 从Swagger文档生成Excel格式测试用例
python main.py --ai-generate --input-doc data/examples/sample_api.json --output-format excel

# 指定输出目录
python main.py --ai-generate --input-doc data/examples/complex_api.md --output-format json --output-dir output/custom
```

### 2. 执行测试用例

```bash
# 运行Excel格式的测试用例
python main.py --type excel

# 运行CSV格式的测试用例
python main.py --type csv

# 运行JSON格式的测试用例
python main.py --type json

# 运行指定文件的测试用例
python main.py --file data/test_cases.xlsx

# 运行指定环境的测试
python main.py --env dev --env staging

# 生成HTML报告
python main.py --generate-report

# 启动Allure报告服务器
python main.py --serve-report
```

## AI功能详细说明

框架集成了强大的AI测试用例生成功能，支持：

- **文档格式**：Markdown、Swagger JSON/YAML
- **生成类型**：正向、反向、边界、结构、路径、权限测试用例
- **输出格式**：Excel、CSV、JSON
- **质量保证**：自动质量验证和修复建议
- **批量处理**：支持多文档批量生成
- **在线文档**：支持在线Swagger文档解析

详细使用方法请参考 [docs/AI_GUIDE.md](docs/AI_GUIDE.md)。

## 命令行参考

详细命令行参数说明请参考 [docs/command_reference.md](command_reference.md)。

## 运行内部单元测试

框架包含全面的内部单元测试，确保各组件稳定可靠：

```bash
# 运行所有内部单元测试
python -m unittest discover internal_tests/

# 运行特定的内部单元测试
python internal_tests/test_engines.py
python internal_tests/test_parsers.py
python internal_tests/test_utils.py
python internal_tests/test_business_logic.py
```

## 开发规范

1. 所有核心功能应位于core目录
2. 工具类应位于utils目录
3. 配置文件应位于config目录
4. 测试用例应位于testcases目录
5. 文档应位于docs目录
6. 内部单元测试应位于internal_tests目录

## 贡献

欢迎提交Issue和Pull Request来改进框架。

## 许可证

[MIT License](LICENSE)
