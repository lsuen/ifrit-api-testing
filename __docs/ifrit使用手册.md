# ifrit自动化测试框架使用手册

## 一、项目简介

ifrit是一个功能强大、灵活易用的API自动化测试框架，支持数据驱动、AI智能生成测试用例等功能。该框架旨在简化API测试流程，提高测试效率和覆盖率。

### 主要特性
1. **数据驱动测试**：支持Excel和CSV格式测试用例
2. **AI智能生成**：从接口文档自动生成全面的测试用例
3. **数据关联**：支持接口间数据传递和变量提取
4. **正则表达式支持**：可使用正则表达式提取数据
5. **配置分离**：环境配置与测试数据配置分离
6. **日志记录**：完整的请求/响应日志记录
7. **Allure报告**：生成美观的测试报告，包含curl命令便于问题复现
8. **多环境支持**：支持多个测试环境配置切换
9. **可扩展架构**：模块化设计，易于扩展

## 二、项目部署

### 2.1 环境要求
- Python 3.8 或更高版本
- pip包管理器
- Git（用于克隆项目）

### 2.2 项目克隆
```bash
git clone https://github.com/your-repo/ifrit.git
cd ifrit
```

### 2.3 依赖安装
推荐使用虚拟环境：
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2.4 配置文件设置

#### 2.4.1 环境配置
编辑 [config/env_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/env_config.ini) 文件，配置不同环境的API基础URL：
```ini
[environment]
base_url = http://your-api-url.com
timeout = 30

[dev]
base_url = http://dev-api-url.com
timeout = 30

[staging]
base_url = http://staging-api-url.com
timeout = 30

[prod]
base_url = https://prod-api-url.com
timeout = 30
```

#### 2.4.2 AI配置（如需使用AI功能）
编辑 [config/ai_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/ai_config.ini) 文件，配置AI服务参数：
```ini
[openai]
api_key = your_openai_api_key
base_url = https://api.openai.com/v1
model = gpt-3.5-turbo
temperature = 0.7
max_tokens = 2000
timeout = 30
```

### 2.5 报告工具配置
如需使用Allure报告，需安装Allure命令行工具：
```bash
# 下载并安装Allure
# Windows (使用Chocolatey):
choco install allure

# 或手动下载Allure并添加到PATH环境变量
```

## 三、项目使用

### 3.1 基本测试执行

#### 3.1.1 运行Excel格式测试用例
```bash
python main.py --type excel
```

#### 3.1.2 运行CSV格式测试用例
```bash
python main.py --type csv
```

#### 3.1.3 运行JSON格式测试用例
```bash
python main.py --type json
```

#### 3.1.4 运行指定文件的测试用例
```bash
python main.py --file data/test_cases.xlsx
```

#### 3.1.5 运行所有测试用例
```bash
python main.py --type all
```

### 3.2 多环境测试
```bash
# 指定单个环境
python main.py --env dev

# 指定多个环境
python main.py --env dev --env staging
```

### 3.3 生成测试报告
```bash
# 生成HTML格式报告
python main.py --generate-report

# 运行测试并启动Allure报告服务器
python main.py --serve-report
```

### 3.4 AI测试用例生成

#### 3.4.1 从Markdown文档生成测试用例
```bash
python main.py --ai-generate --input-doc data/examples/api_document.md --output-format csv
```

#### 3.4.2 从Swagger文档生成测试用例
```bash
python main.py --ai-generate --input-doc data/examples/swagger.json --output-format excel
```

#### 3.4.3 指定输出目录
```bash
python main.py --ai-generate --input-doc data/examples/api_document.md --output-format json --output-dir output/custom
```

#### 3.4.4 指定在线Swagger端点
```bash
python main.py --ai-generate --swagger-endpoint https://petstore.swagger.io/v2/swagger.json --output-format csv
```

### 3.5 测试数据格式

#### 3.5.1 Excel格式示例
| case_id | case_name | method | url | headers | params | body | expected_status | expected_content | json_path | expected_json_value |
|---------|-----------|--------|-----|---------|--------|------|-----------------|------------------|-----------|--------------------|
| TC001 | 用户登录测试 | POST | /api/login | {"Content-Type":"application/json"} | | {"username":"test","password":"123456"} | 200 | | $.token | | |

#### 3.5.2 CSV格式示例
```csv
case_id,case_name,method,url,headers,params,body,expected_status,expected_content,json_path,expected_json_value
TC001,用户登录测试,POST,/api/login,"{""Content-Type"":""application/json""}",,"{""username"":""test"",""password"":""123456""}",200,,,
```

### 3.6 变量提取和关联
框架支持从响应中提取变量并在后续请求中使用：
- 使用正则表达式提取：`"${regex:pattern}"` 
- 使用JSONPath提取：`"${jsonpath:$.field}"`

## 四、常见问题

### 4.1 环境配置问题
**问题**：提示找不到配置文件或配置无效
**解决**：检查 [config/env_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/env_config.ini) 文件是否存在且格式正确

### 4.2 依赖包问题
**问题**：运行时报ImportError错误
**解决**：重新安装依赖包
```bash
pip install -r requirements.txt
```

### 4.3 Allure报告问题
**问题**：无法生成Allure报告
**解决**：确保Allure命令行工具已正确安装并添加到PATH

### 4.4 AI功能问题
**问题**：AI生成功能报错或无法连接
**解决**：检查AI配置文件中的API密钥和端点配置

### 4.5 测试用例执行问题
**问题**：测试用例执行失败
**解决**：
1. 检查API基础URL配置
2. 检查测试用例格式是否正确
3. 查看日志文件获取详细错误信息

## 五、注意事项

### 5.1 安全性
- 不要在配置文件中硬编码敏感信息（如API密钥）
- 使用环境变量或安全的配置管理系统存储敏感信息

### 5.2 性能
- 避免在单个测试用例中执行过多的API调用
- 合理设置请求超时时间
- 使用数据驱动的方式组织大量测试用例

### 5.3 维护性
- 保持测试用例的独立性
- 使用有意义的测试用例ID和名称
- 定期清理不再使用的测试用例

### 5.4 最佳实践
- 为每个API端点编写正向、反向、边界测试用例
- 使用Allure报告功能追踪测试结果
- 利用AI功能快速生成测试用例

## 六、其他资源

### 6.1 项目结构说明
```
ifrit/
├── config/                  # 配置文件目录
├── core/                    # 核心功能目录
├── utils/                   # 工具类目录
├── drivers/                 # 测试驱动目录
├── data/                    # 测试数据目录
├── __docs/                  # 文档目录
├── logs/                    # 日志目录
├── reports/                 # 测试报告目录
├── main.py                  # 主程序入口
├── ai_case_generator.py     # AI测试用例生成器
└── pytest.ini               # Pytest配置文件
```

### 6.2 调试技巧
- 使用 `--verbose` 参数查看详细执行过程
- 检查 [logs/](file:///C:/CodeFiles/PyProjects/ifrit-apitest/logs) 目录下的日志文件
- 使用独立的AI生成脚本进行调试：
  ```bash
  python ai_case_generator.py --help
  ```

### 6.3 扩展功能
- 可以通过修改 [core/](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core) 目录下的模块扩展功能
- 支持自定义测试数据格式和解析器
- 可以集成其他报告工具替代Allure