# AI智能测试用例生成指南

> **新手推荐：** 先看 **[用户详细使用手册.md](../用户详细使用手册.md)** 第 6～7 节（AI 生成与 `--chat` 交互模式）。  
> 本文档面向需要调整生成策略、prompt 的研发同学。

本指南详细介绍如何使用框架的AI功能从接口文档自动生成全面的测试用例。

## 目录

- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [支持的文档格式](#支持的文档格式)
- [生成策略](#生成策略)
- [使用方式](#使用方式)
- [在线Swagger文档](#在线swagger文档)
- [生成用例直接运行](#生成用例直接运行)
- [高级功能](#高级功能)
- [故障排除](#故障排除)

## 快速开始

### 1. 配置AI服务

编辑 `config/ai_config.ini` 文件：

```ini
[openai]
# 本地OpenAI服务配置
base_url = http://localhost:8000
model = gpt-3.5-turbo
api_key = your_api_key_here
temperature = 0.7
max_tokens = 2000
timeout = 30

[generation]
# 生成策略配置
positive_cases_count = 3
negative_cases_count = 2
boundary_cases_count = 2
structure_cases_count = 1
path_cases_count = 2
include_auth_cases = true
```

### 2. 准备接口文档

框架支持两种文档格式：

**Markdown格式示例：**
```markdown
## 用户注册接口

### POST /api/auth/register

注册新用户账号

**请求参数：**
- username (string, required): 用户名
- email (string, required): 邮箱地址
- password (string, required): 密码

**响应示例：**
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user_id": 12345,
    "username": "testuser"
  }
}
```

**Swagger JSON格式：**
```json
{
  "openapi": "3.0.0",
  "paths": {
    "/api/users": {
      "get": {
        "summary": "获取用户列表",
        "parameters": [
          {
            "name": "page",
            "in": "query",
            "schema": {"type": "integer"}
          }
        ],
        "responses": {
          "200": {
            "description": "成功"
          }
        }
      }
    }
  }
}
```

### 3. 生成测试用例

使用主程序生成：
```bash
python main.py --ai-generate --input-doc data/examples/complex_api.md --output-format csv
```

使用独立脚本生成：
```bash
python ai_case_generator.py data/examples/complex_api.md --format excel --preview
```

## 配置说明

### AI服务配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `base_url` | OpenAI API端点 | `http://localhost:8000` |
| `api_key` | API密钥（优先从环境变量读取） | - |
| `model` | 使用的模型 | `gpt-3.5-turbo` |
| `temperature` | 生成随机性 | `0.7` |
| `max_tokens` | 最大token数 | `2000` |
| `timeout` | 请求超时时间 | `30` |

### 生成策略配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `positive_cases_count` | 正向测试用例数量 | `3` |
| `negative_cases_count` | 反向测试用例数量 | `2` |
| `boundary_cases_count` | 边界测试用例数量 | `2` |
| `structure_cases_count` | 结构测试用例数量 | `1` |
| `path_cases_count` | 路径测试用例数量 | `2` |
| `include_auth_cases` | 是否包含权限测试用例 | `true` |

### 输出配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `default_output_dir` | 默认输出目录 | `data/ai_generated` |
| `add_timestamp` | 是否添加时间戳 | `true` |
| `file_prefix` | 文件前缀 | `ai_` |
| `quality_check` | 是否进行质量检查 | `true` |
| `conflict_resolution` | 文件冲突处理方式 | `ask` |

## 支持的文档格式

### 1. Markdown文档

支持标准的API文档Markdown格式，自动识别：
- 接口标题和描述
- HTTP方法和路径
- 请求参数
- 响应示例
- 状态码说明

**示例文档：** `data/examples/complex_api.md`

### 2. Swagger文档

支持OpenAPI 3.0和Swagger 2.0格式：
- JSON格式：`.json`
- YAML格式：`.yaml` 或 `.yml`
- 在线文档：通过URL访问

**示例文档：** `data/examples/ecommerce_swagger.json`

## 生成策略

框架会为每个API接口生成多种类型的测试用例：

### 1. 正向测试用例 (Positive Cases)
- 验证正常业务流程
- 使用有效参数和数据
- 期望返回成功状态码

### 2. 反向测试用例 (Negative Cases)
- 验证异常处理能力
- 使用无效参数和数据
- 测试错误场景

### 3. 边界测试用例 (Boundary Cases)
- 测试参数边界值
- 最大值、最小值、空值
- 特殊字符和格式

### 4. 结构测试用例 (Structure Cases)
- 验证请求/响应结构
- 必填字段验证
- 数据类型验证

### 5. 路径测试用例 (Path Cases)
- 测试不同的执行路径
- 条件分支覆盖
- 业务逻辑验证

### 6. 权限测试用例 (Auth Cases)
- 认证和授权测试
- 无权限访问测试
- 权限边界测试

## 使用方式

### 方式一：主程序集成

```bash
# 基础生成
python main.py --ai-generate --input-doc __docs/api.md

# 指定输出格式
python main.py --ai-generate --input-doc __docs/api.md --output-format excel

# 指定输出目录
python main.py --ai-generate --input-doc __docs/api.md --output-dir custom_output

# 指定Swagger端点
python main.py --ai-generate --input-doc swagger.json --swagger-endpoint /api/users --swagger-endpoint /api/orders
```

### 方式二：独立脚本

```bash
# 基础生成
python ai_case_generator.py __docs/api.md

# 预览模式
python ai_case_generator.py __docs/api.md --preview

# 批量处理
python ai_case_generator.py __docs/*.md --merge

# 交互式模式
python ai_case_generator.py --interactive
```

### 命令行参数说明

#### 主程序参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--ai-generate` | 启用AI生成功能 | - |
| `--input-doc` | 输入文档路径 | `docs/api.md` |
| `--swagger-endpoint` | 指定Swagger端点 | `--swagger-endpoint /api/users` |
| `--output-format` | 输出格式 | `csv`, `excel`, `json` |
| `--output-dir` | 输出目录 | `custom_output` |

#### 独立脚本参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `input_docs` | 输入文档路径（支持通配符） | `docs/*.md` |
| `--endpoints` | 指定端点 | `--endpoints /api/users` |
| `--format` | 输出格式 | `excel`, `csv`, `json` |
| `--output-dir` | 输出目录 | `custom_output` |
| `--merge` | 合并多文档输出 | - |
| `--preview` | 预览模式 | - |
| `--interactive` | 交互式模式 | - |

## 在线Swagger文档

框架支持直接从在线Swagger文档生成测试用例：

### 1. 使用在线JSON文档

```bash
# 下载在线Swagger文档
curl -o swagger.json http://192.168.31.129:5000/apispec_1.json

# 生成测试用例
python ai_case_generator.py swagger.json --format excel
```

### 2. 使用wget下载

```bash
# Windows (需要安装wget)
wget http://192.168.31.129:5000/apispec_1.json -O swagger.json

# 或使用PowerShell
Invoke-WebRequest -Uri "http://192.168.31.129:5000/apispec_1.json" -OutFile "swagger.json"
```

### 3. 一键下载并生成

创建批处理脚本 `generate_from_online.bat`：

```batch
@echo off
echo 正在下载在线Swagger文档...
curl -o temp_swagger.json http://192.168.31.129:5000/apispec_1.json

echo 正在生成测试用例...
python ai_case_generator.py temp_swagger.json --format excel --preview

echo 清理临时文件...
del temp_swagger.json

echo 完成！
pause
```

### 4. 指定特定端点

```bash
# 只生成特定端点的测试用例
python ai_case_generator.py swagger.json --endpoints /api/users --endpoints /api/orders --format csv
```

### 5. 在线文档示例

常见的在线Swagger文档URL格式：
- Flask应用：`http://host:port/apispec_1.json`
- FastAPI应用：`http://host:port/openapi.json`
- Spring Boot应用：`http://host:port/v3/api-docs`
- Django应用：`http://host:port/swagger.json`

## 生成用例直接运行

AI生成的测试用例可以直接用于测试执行：

### 1. 生成并运行CSV用例

```bash
# 步骤1：生成CSV格式测试用例
python main.py --ai-generate --input-doc data/examples/complex_api.md --output-format csv

# 步骤2：运行生成的测试用例
python main.py --type csv --generate-report
```

### 2. 生成并运行Excel用例

```bash
# 步骤1：生成Excel格式测试用例
python ai_case_generator.py data/examples/ecommerce_swagger.json --format excel

# 步骤2：运行Excel测试用例
python main.py --type excel --generate-report
```

### 3. 指定具体文件运行

```bash
# 运行指定的AI生成文件
python main.py --file data/ai_generated/csv_data/ai_complex_api_20240113_143022.csv --generate-report
```

### 4. 批量生成和运行

创建自动化脚本 `auto_test.py`：

```python
#!/usr/bin/env python
import subprocess
import glob
import os

def generate_and_run_tests():
    """生成测试用例并运行"""
    
    # 1. 生成测试用例
    docs = glob.glob("data/examples/*.md") + glob.glob("data/examples/*.json")
    
    for doc in docs:
        print(f"正在处理文档: {doc}")
        cmd = [
            "python", "ai_case_generator.py", 
            doc, "--format", "csv"
        ]
        subprocess.run(cmd)
    
    # 2. 运行所有生成的测试用例
    print("开始运行测试用例...")
    cmd = ["python", "main.py", "--type", "csv", "--generate-report"]
    subprocess.run(cmd)
    
    print("测试完成！")

if __name__ == "__main__":
    generate_and_run_tests()
```

运行自动化脚本：
```bash
python auto_test.py
```

### 5. 环境配置

确保测试环境配置正确：

```ini
# config/env_config.ini
[environment]
base_url = http://192.168.31.129:5000
timeout = 30

[api_test]
base_url = http://192.168.31.129:5000
timeout = 30
```

运行时指定环境：
```bash
python main.py --type csv --env api_test --generate-report
```

## 高级功能

### 1. 交互式生成

使用交互式模式进行更灵活的配置：

```bash
python ai_case_generator.py --interactive
```

交互式模式支持：
- 选择文档类型和路径
- 配置生成参数
- 预览生成结果
- 自定义输出设置

### 2. 批量处理

处理多个文档并合并输出：

```bash
# 处理目录下所有Markdown文档
python ai_case_generator.py __docs/*.md --merge --format excel

# 处理多种格式文档
python ai_case_generator.py __docs/api.md __docs/swagger.json --merge
```

### 3. 质量验证

框架自动进行质量验证并提供修复建议：

- **完整性检查**：验证必要字段是否存在
- **格式验证**：检查JSON格式和数据类型
- **逻辑一致性**：验证测试逻辑是否合理
- **兼容性检查**：确保与现有框架兼容

### 4. 自定义模板

可以通过修改配置文件自定义生成模板：

```ini
[prompts]
system_prompt = 你是一个专业的API测试工程师...
positive_template = 为以下接口生成正向测试用例...
negative_template = 为以下接口生成反向测试用例...
```

### 5. 输出格式转换

生成的测试用例支持多种格式：

```bash
# 生成Excel格式
python ai_case_generator.py api.md --format excel

# 生成CSV格式
python ai_case_generator.py api.md --format csv

# 生成JSON格式
python ai_case_generator.py api.md --format json
```

## 故障排除

### 1. AI服务连接问题

**问题**：无法连接到AI服务
```
ERROR - AI接口调用失败: Connection refused
```

**解决方案**：
- 检查AI服务是否启动：`curl http://localhost:8000/health`
- 验证配置文件中的`base_url`是否正确
- 检查网络连接和防火墙设置

### 2. 文档解析失败

**问题**：无法解析文档内容
```
ERROR - 未能从文档中解析出任何API接口
```

**解决方案**：
- 检查文档格式是否符合要求
- 验证文件路径是否正确
- 查看示例文档格式：`data/examples/`

### 3. 生成用例质量问题

**问题**：生成的测试用例质量评分较低

**解决方案**：
- 调整生成策略配置
- 优化输入文档的详细程度
- 使用质量验证功能查看具体问题

### 4. 输出文件问题

**问题**：无法保存生成的测试用例

**解决方案**：
- 检查输出目录权限
- 确保磁盘空间充足
- 验证文件路径格式

### 5. 在线文档访问问题

**问题**：无法访问在线Swagger文档

**解决方案**：
```bash
# 测试网络连接
curl -I http://192.168.31.129:5000/apispec_1.json

# 检查响应内容
curl http://192.168.31.129:5000/apispec_1.json | head -20

# 使用代理（如果需要）
curl --proxy http://proxy:port http://192.168.31.129:5000/apispec_1.json
```

### 6. 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `Connection refused` | 无法连接AI服务 | 检查服务状态和配置 |
| `Invalid JSON` | JSON格式错误 | 检查文档格式 |
| `API key invalid` | API密钥无效 | 更新配置文件或环境变量 |
| `Timeout` | 请求超时 | 增加超时时间配置 |
| `Rate limit exceeded` | 请求频率过高 | 降低并发请求数量 |

### 7. 调试模式

启用详细日志进行调试：

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 运行生成器
python ai_case_generator.py api.md --format csv
```

### 8. 获取帮助

```bash
# 查看主程序帮助
python main.py --help

# 查看独立脚本帮助
python ai_case_generator.py --help

# 查看配置示例
cat config/ai_config.ini
```

## 最佳实践

1. **文档准备**：确保接口文档详细完整，包含参数说明和响应示例
2. **配置优化**：根据项目需求调整生成策略和参数
3. **质量检查**：始终启用质量验证功能
4. **版本控制**：将生成的测试用例纳入版本控制
5. **持续集成**：将AI生成集成到CI/CD流程中
6. **定期更新**：随着接口变更及时更新文档和重新生成用例

通过本指南，您可以充分利用框架的AI功能，大幅提升测试用例编写效率和覆盖率。