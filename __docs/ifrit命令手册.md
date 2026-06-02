# ifrit自动化测试框架命令手册

> **命令速查（含鉴权说明）：** [用户详细使用手册.md](../用户详细使用手册.md#12-命令速查表)  
> 本文档为完整参数列表，部分默认值以当前代码为准（AI 输出目录默认为 `fixtures/ai/csv`）。

## 一、参数介绍

### 1.1 基础参数
- `--serve-report`: 运行测试并启动Allure报告服务器
- `--generate-report`: 生成HTML格式的Allure报告
- `--type`: 指定测试类型，可选值：`excel`、`csv`、`all`、`json`
- `--file`: 指定测试文件路径
- `--env`: 指定运行环境，可以多次使用以指定多个环境
- `--suite`: 用例套件 `manual` / `ai` / `smoke` / `all`
- `--global-auth`: 启用全局鉴权（`config/settings/auth.ini`，默认 test/123456）
- `--clean`: 清理 `logs` / `reports` / `all`
- `--keep-days` / `--dry-run`: 清理策略

### 1.2 AI功能参数
- `--ai-generate`: 启用AI测试用例生成功能
- `--input-doc`: 指定输入文档路径（支持Markdown、Swagger JSON/YAML格式）
- `--input-url`: 指定远程文档 URL（Apifox MD / Swagger JSON 等，自动缓存到 `api_docs/cache/`）
- `--swagger-endpoint`: 指定要解析的Swagger端点，可以多次使用
- `--skill`: 指定 Agent Skill（如 `case_generation`、`doc_url_generation`）
- `--chat`: 进入 AI 交互模式；可选跟随单行命令
- `--output-format`: 指定生成的测试用例格式，可选值：`excel`、`csv`、`json`（默认：csv）
- `--output-dir`: 指定输出目录（默认：`fixtures/ai/csv`）

## 二、基本命令

### 2.1 测试执行命令

#### 2.1.1 运行Excel格式测试用例
```bash
python main.py --type excel
```

#### 2.1.2 运行CSV格式测试用例
```bash
python main.py --type csv
```

#### 2.1.3 运行JSON格式测试用例
```bash
python main.py --type json
```

#### 2.1.4 运行所有测试用例
```bash
python main.py --type all
```

#### 2.1.5 运行指定文件测试用例
```bash
python main.py --file data/test_cases.xlsx
```

#### 2.1.6 指定单个环境运行测试
```bash
python main.py --env dev
```

#### 2.1.7 指定多个环境运行测试
```bash
python main.py --env dev --env staging
```

### 2.2 报告生成命令

#### 2.2.1 生成HTML报告
```bash
python main.py --generate-report
```

#### 2.2.2 运行测试并启动报告服务器
```bash
python main.py --serve-report
```

#### 2.2.3 运行测试并生成报告
```bash
python main.py --type csv --generate-report
```

### 2.3 AI生成命令

#### 2.3.1 从Markdown文档生成CSV格式测试用例
```bash
python main.py --ai-generate --input-doc data/examples/api_document.md --output-format csv
```

#### 2.3.2 从Swagger文档生成Excel格式测试用例
```bash
python main.py --ai-generate --input-doc data/examples/swagger.json --output-format excel
```

#### 2.3.3 从在线Swagger端点生成JSON格式测试用例
```bash
python main.py --ai-generate --swagger-endpoint https://api.example.com/swagger.json --output-format json
```

#### 2.3.4 指定输出目录
```bash
python main.py --ai-generate --input-doc data/examples/api_document.md --output-format excel --output-dir output/my_tests
```

## 三、组合命令

### 3.1 运行测试并生成报告
```bash
# 运行Excel格式测试并生成报告
python main.py --type excel --generate-report

# 运行CSV格式测试并启动报告服务器
python main.py --type csv --serve-report

# 指定环境运行测试并生成报告
python main.py --type json --env dev --generate-report
```

### 3.2 AI生成并立即执行
```bash
# 1. 生成测试用例
python main.py --ai-generate --input-doc data/examples/api_document.md --output-format csv

# 2. 运行生成的测试用例
python main.py --file data/ai_generated/csv_data/ai_api_document_YYYYMMDD_HHMMSS.csv
```

### 3.3 多环境测试执行
```bash
# 在多个环境中运行Excel格式测试
python main.py --type excel --env dev --env staging --env prod --generate-report

# 在多个环境中运行指定文件测试
python main.py --file data/test_cases.xlsx --env dev --env prod --serve-report
```

### 3.4 复杂组合示例
```bash
# 在开发和预发布环境运行CSV测试，并生成HTML报告
python main.py --type csv --env dev --env staging --generate-report

# 从在线API文档生成Excel测试用例，然后在生产环境执行
python main.py --ai-generate --swagger-endpoint https://api.example.com/swagger.json --output-format excel
python main.py --env prod --type excel --serve-report

# 运行所有测试并启动报告服务器
python main.py --type all --serve-report
```

## 四、常见问题

### 4.1 参数冲突问题
**问题**：某些参数不能同时使用
**解决**：
- `--type` 和 `--file` 参数通常不会冲突，但指定 `--file` 时会忽略 `--type` 参数
- `--serve-report` 和 `--generate-report` 可以同时使用，但会按顺序执行

### 4.2 文件路径问题
**问题**：提示文件不存在
**解决**：
- 确保文件路径正确，使用相对路径或绝对路径
- 检查文件扩展名是否与实际格式匹配
- 验证文件是否存在且可读

### 4.3 环境参数问题
**问题**：环境参数不生效
**解决**：
- 确认环境名称在 [config/env_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/env_config.ini) 中存在
- 环境参数区分大小写，注意拼写
- 多个环境参数会被依次应用

### 4.4 AI功能参数问题
**问题**：AI生成功能缺少必要参数
**解决**：
- 使用 `--ai-generate` 时必须指定 `--input-doc` 参数
- 确认输入文档格式正确且内容有效
- 检查AI配置文件是否正确设置

### 4.5 Allure报告问题
**问题**：报告生成失败
**解决**：
- 确保Allure命令行工具已安装
- 检查 `reports/` 目录是否有写入权限
- 验证是否有足够的磁盘空间

## 五、注意事项

### 5.1 参数使用注意事项
- `--env` 参数可以多次使用，所有指定的环境配置会被合并应用
- `--ai-generate` 参数启用AI功能时，其他测试执行参数将被忽略
- 输出格式参数只在AI生成模式下有效

### 5.2 路径和文件注意事项
- 文件路径支持相对路径和绝对路径
- 推荐使用相对路径以增强可移植性
- 确保路径中不包含特殊字符

### 5.3 性能注意事项
- 运行大量测试用例时，考虑分批执行以避免内存问题
- 生成报告可能需要较长时间，特别是对于大型测试套件
- AI生成功能可能需要网络连接，视API响应时间而定

### 5.4 安全注意事项
- 不要在命令行中直接传递敏感信息（如API密钥）
- 使用配置文件或环境变量管理敏感数据
- 定期清理生成的测试报告以释放磁盘空间

## 六、其他

### 6.1 调试技巧
- 使用 `-v` 参数（pytest参数）获取更详细的输出
- 检查 `logs/` 目录下的日志文件获取更多信息
- 对于AI生成功能，可以在配置文件中启用详细日志

### 6.2 高级用法
- 可以结合shell脚本实现自动化测试流程
- 支持CI/CD集成，适合持续集成环境
- 可以通过环境变量覆盖配置文件中的设置

### 6.3 帮助信息
要获取最新帮助信息，可以直接运行：
```bash
python main.py --help
```

### 6.4 错误代码含义
- 0: 成功执行
- 1: 一般错误
- 2: 参数错误
- 3: 配置错误
- 4: 文件访问错误
- 5: AI服务错误