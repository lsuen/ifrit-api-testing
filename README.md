# 接口自动化测试框架

这是一个基于Python、Pytest和Allure的接口自动化测试框架，支持Excel和CSV格式测试用例管理和数据关联。

## 目录结构

```
api_automation_framework/
├── config/                  # 配置文件目录
│   ├── __init__.py
│   ├── config.py            # 全局配置
│   ├── env_config.ini       # 环境配置
│   └── test_data_config.ini # 测试数据配置
├── core/                    # 核心功能目录
│   ├── __init__.py
│   ├── request_handler.py   # 请求处理工具
│   ├── assert_handler.py    # 断言工具
│   ├── data_handler.py      # 数据处理器(含关联和正则)
│   └── test_executor.py     # 测试执行器（统一执行逻辑）
├── utils/                   # 工具类目录
│   ├── __init__.py
│   ├── excel_handler.py     # Excel操作工具
│   ├── logger.py            # 日志工具
│   └── common_utils.py      # 通用工具
├── testcases/               # 测试用例目录
│   ├── __init__.py
│   ├── conftest.py          # Pytest配置和fixture
│   ├── test_api_excel_driver.py  # Excel测试驱动
│   └── test_api_csv_driver.py    # CSV测试驱动
├── data/                    # 测试数据目录
├── logs/                    # 日志目录
├── reports/                 # 测试报告目录
├── main.py                  # 主程序入口
└── pytest.ini               # Pytest配置文件
```

## 功能特性

1. **数据驱动测试**：支持Excel和CSV格式测试用例
2. **数据关联**：支持接口间数据传递和变量提取
3. **正则表达式支持**：可使用正则表达式提取数据
4. **配置分离**：环境配置与测试数据配置分离
5. **日志记录**：完整的请求/响应日志记录
6. **Allure报告**：生成美观的测试报告，包含curl命令便于问题复现，使用case_name作为测试项标识
7. **多环境支持**：支持多个测试环境配置切换
8. **可扩展架构**：模块化设计，易于扩展
9. **多值变量提取**：支持一次提取多个变量并分别存储

## 安装依赖(建议python version>=3.7)

<!-- 点击运行: 安装项目依赖 -->
```bash
pip install -r requirements.txt 
```

确保已安装Allure命令行工具：
- macOS: `brew install allure`
- Windows: `choco install allure` 或从官网下载安装
- Linux: 下载二进制包并加入PATH

## 快速开始

### 1. 配置环境

编辑 `config/env_config.ini` 文件配置基础URL和超时时间：

```ini
[environment]
base_url = http://5912.org:6666
timeout = 30

[api_dev]
base_url = http://192.168.31.78:6666
timeout = 30

[api_prod]
base_url = https://api.production.com
timeout = 30
```

### 2. 编写测试用例

在 `data/test_cases.xlsx` 或 `data/test_cases.csv` 中编写测试用例。

#### Excel测试用例格式支持以下列：

- `id`: 用例ID
- `name`: 用例名称
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
- `validate`: 断言表达式
- `enabled`: 是否启用 (1/0)

#### CSV测试用例格式

CSV格式与Excel格式相同，但以逗号分隔，注意JSON字段需要正确转义。

### 3. 运行测试

#### 基础运行命令

<!-- 点击运行: 运行所有测试 -->
```bash
python main.py
```

<!-- 点击运行: 运行测试并生成Allure报告 -->
```bash
python main.py --generate-report
```

<!-- 点击运行: 运行测试并启动Allure报告服务器 -->
```bash
python main.py --serve-report
```

#### 指定测试类型

<!-- 点击运行: 只运行Excel测试用例 -->
```bash
python main.py --type excel
```

<!-- 点击运行: 只运行CSV测试用例 -->
```bash
python main.py --type csv
```

<!-- 点击运行: 运行所有测试（默认） -->
```bash
python main.py --type all
```

#### 指定测试文件

<!-- 点击运行: 运行指定的Excel文件 -->
```bash
python main.py --file data/excel_data/test_cases.xlsx
```

<!-- 点击运行: 运行指定的CSV文件 -->
```bash
python main.py --file data/csv_data/test_cases.csv
```

#### 指定运行环境

框架支持多环境配置，可以通过 `--env` 参数指定运行环境：

<!-- 点击运行: 使用开发环境配置运行测试 -->
```bash
python main.py --env api_dev
```

<!-- 点击运行: 使用生产环境配置运行测试 -->
```bash
python main.py --env api_prod
```

<!-- 点击运行: 指定多个环境（按优先级顺序） -->
```bash
python main.py --env api_prod --env api_staging --env api_dev
```

环境配置按指定顺序查找，使用第一个找到的有效配置。如果未找到指定环境的配置，则回退到默认的 [environment] 部分配置。

#### 组合使用参数

<!-- 点击运行: 运行Excel测试并生成报告 -->
```bash
python main.py --type excel --generate-report
```

<!-- 点击运行: 运行指定文件并启动报告服务器 -->
```bash
python main.py --file data/test_cases.xlsx --serve-report
```

<!-- 点击运行: 使用开发环境运行CSV测试并生成HTML报告 -->
```bash
python main.py --type csv --env api_dev --generate-report
```

### 4. 查看测试报告

测试报告分为两种格式：

1. **交互式报告**：使用Allure服务器查看
   <!-- 点击运行: 启动Allure报告服务器 -->
   ```bash
   python main.py --serve-report
   ```

2. **静态HTML报告**：生成HTML文件查看
   <!-- 点击运行: 生成静态HTML报告 -->
   ```bash
   python main.py --generate-report
   ```
   然后打开 `reports/html/index.html`

在Allure报告中，每个测试项都会显示为"用例ID - 用例名称"的格式，便于识别具体的测试用例。

### 5. 高级功能

#### 变量提取与使用

1. 在测试用例中配置 `extract_key` 和 `save_var_name` 列来提取变量
2. 在后续用例中使用 `${variable_name}` 或 `{{variable_name}}` 引用变量

#### 正则表达式提取

在 `extract_key` 列中使用 `regex:your_pattern` 格式来提取数据

#### 多值变量提取

框架支持在单次提取中获取多个变量并分别存储：

1. 在 `extract_key` 列中使用分号分隔多个提取表达式
2. 使用 `变量名=提取路径` 的格式为提取值指定变量名
3. 例如：`token=token; message=debug[0].path1` 将分别存储token和message两个变量

#### 断言配置

在 `validate` 列中配置断言表达式，支持：
- JSON路径断言：`json.key=value`
- 正则断言：`regex.pattern=expected_value`

## 使用curltocase_client.py工具

框架还提供了一个图形界面工具 `curltocase_client.py`，可以将curl命令转换为测试用例：

<!-- 点击运行: 启动curl转测试用例工具 -->
```bash
python curltocase_client.py
```

运行后会打开图形界面，可以：
1. 粘贴curl命令
2. 选择目标文件(csv或excel)
3. 自动解析并写入测试用例

## 常见问题

### 1. Allure命令未找到

确保已安装Allure命令行工具并加入系统PATH。

### 2. Excel文件无法读取

确保Excel文件格式正确，路径无误，且已安装必要的依赖包：
<!-- 点击运行: 安装Excel处理依赖 -->
```bash
pip install openpyxl xlrd
```

### 3. 测试用例未执行

检查测试用例中 `enabled` 列是否设置为1，且文件路径正确。

### 4. 变量无法传递

确保前置用例正确提取变量，且后续用例正确引用变量名。

## 扩展框架功能（面向专业人员）

本框架采用模块化设计，易于扩展和定制。以下是扩展框架功能的几种方式：

### 1. 添加新的数据源支持

框架当前支持Excel和CSV格式的测试用例。要添加新的数据源（如JSON、数据库等）：

1. 在 `core/data_handler.py` 中扩展数据处理逻辑
2. 在 `config/config.py` 中添加新的配置选项
3. 创建新的测试驱动文件（参考 `testcases/test_api_excel_driver.py` 和 `testcases/test_api_csv_driver.py`）

### 2. 扩展断言类型

框架支持多种断言类型，可以通过以下方式添加新的断言类型：

1. 修改 `core/assert_handler.py` 文件中的 `AssertHandler` 类
2. 添加新的断言解析逻辑
3. 在测试用例的 `validate` 字段中使用新的断言格式

### 3. 增强请求处理功能

框架使用 `core/request_handler.py` 处理HTTP请求，可以通过以下方式增强：

1. 添加新的认证机制（如OAuth、JWT等）
2. 支持文件上传等复杂请求
3. 添加请求重试机制
4. 增加请求中间件支持

### 4. 自定义报告格式

框架使用Allure生成报告，但也可以通过以下方式自定义：

1. 实现新的报告生成器
2. 添加自定义的报告模板
3. 集成其他报告工具（如ExtentReports）

### 5. 集成CI/CD

框架可以轻松集成到CI/CD流程中：

1. 在Jenkins、GitLab CI等平台中配置测试任务
2. 配置测试报告收集和展示
3. 设置测试结果通知机制

### 6. 性能测试扩展

框架主要面向功能测试，但也可以扩展支持性能测试：

1. 集成Locust或JMeter
2. 添加并发测试支持
3. 实现性能指标收集和分析

### 7. 开发自定义工具

框架提供了良好的扩展点，可以开发以下自定义工具：

1. 测试数据生成器
2. 测试结果分析工具
3. 自动化测试维护工具
4. 测试覆盖率分析工具

通过以上方式，您可以根据项目需求对框架进行定制和扩展，以满足更复杂的测试场景。