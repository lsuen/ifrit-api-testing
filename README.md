# 接口自动化测试框架

这是一个基于Python、Pytest和Allure的接口自动化测试框架，支持Excel格式测试用例管理和数据关联。

## 目录结构

```
api_automation_framework/
├── config/                  # 配置文件目录
│   ├── __init__.py
│   ├── config.py            # 全局配置
│   ├── env_config.ini       # 环境配置
│   └── test_data_config.ini # 测试数据配置
├── data/                    # 测试数据目录
│   └── test_cases.xlsx      # Excel测试用例
├── core/                    # 核心功能目录
│   ├── __init__.py
│   ├── request_handler.py   # 请求处理工具
│   ├── assert_handler.py    # 断言工具
│   └── data_handler.py      # 数据处理器(含关联和正则)
├── utils/                   # 工具类目录
│   ├── __init__.py
│   ├── excel_handler.py     # Excel操作工具
│   ├── logger.py            # 日志工具
│   └── common_utils.py      # 通用工具
├── testcases/               # 测试用例目录
│   ├── __init__.py
│   ├── conftest.py          # Pytest配置和fixture
│   └── test_api_excel.py    # 测试用例文件
├── logs/                    # 日志目录
├── reports/                 # 测试报告目录
├── main.py                  # 主程序入口
└── pytest.ini               # Pytest配置文件
```

## 功能特性

1. **数据驱动测试**：支持Excel格式测试用例
2. **数据关联**：支持接口间数据传递和变量提取
3. **正则表达式支持**：可使用正则表达式提取数据
4. **配置分离**：环境配置与测试数据配置分离
5. **日志记录**：完整的请求/响应日志记录
6. **Allure报告**：生成美观的测试报告
7. **可扩展架构**：模块化设计，易于扩展

## 安装依赖

```bash
pip install pytest requests pandas openpyxl allure-pytest
```

## 使用方法

### 1. 配置环境

编辑 `config/env_config.ini` 文件配置基础URL和超时时间：

```ini
[environment]
base_url = http://5912.org:6666
timeout = 30
```

### 2. 编写测试用例

在 `data/test_cases.xlsx` 中编写测试用例，支持以下列：

- `case_id`: 用例ID
- `case_name`: 用例名称
- `enabled`: 是否启用 (yes/no)
- `method`: HTTP方法 (GET/POST/PUT/DELETE)
- `url`: 请求路径
- `headers`: 请求头 (JSON格式)
- `params`: URL参数 (JSON格式)
- `body`: 请求体 (JSON格式)
- `expected_status`: 期望状态码
- `expected_content`: 期望包含的内容
- `json_path`: JSON路径断言路径
- `expected_json_value`: 期望的JSON值
- `extract_key`: 提取键路径 (支持正则:regex:pattern格式)
- `save_var_name`: 保存的变量名

### 3. 运行测试

```bash
# 运行所有测试
python main.py

# 运行所有用例并打印
pytest testcases/test_all_drivers.py -v

# 运行测试并生成报告
python main.py --serve-report
```

### 4. 查看报告

```bash
# 启动Allure报告服务
allure serve reports/allure_reports
```

## 数据关联示例

1. 在用例A中设置：
   - `extract_key`: token
   - `save_var_name`: user_token

2. 在用例B中使用：
   - 在需要的地方使用 `{{user_token}}` 占位符

## 正则表达式提取示例

- `extract_key`: regex:"token":"([^"]+)"
- `save_var_name`: extracted_token

这将从响应中提取token的值。