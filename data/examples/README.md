# AI测试用例生成器示例文档

本目录包含了用于演示AI测试用例生成功能的示例文档。

## 文档列表

### 1. sample_api.md
基础API文档示例，包含：
- 用户登录接口 (POST /api/user/login)
- 获取用户信息接口 (GET /api/user/profile)

**特点：**
- 简单的Markdown格式
- 包含基本的参数表格
- 有认证要求的接口

### 2. sample_api.json
对应的Swagger JSON格式文档，与sample_api.md内容相同。

**特点：**
- 标准Swagger 2.0格式
- 包含安全定义
- 详细的响应模式

### 3. complex_api.md
复杂API文档示例，包含：
- 用户注册接口 (POST /api/auth/register)
- 获取用户详情接口 (GET /api/users/{user_id})
- 更新用户资料接口 (PUT /api/users/{user_id}/profile)
- 删除用户接口 (DELETE /api/users/{user_id})
- 获取文章列表接口 (GET /api/posts)

**特点：**
- 多种HTTP方法
- 路径参数和查询参数
- 复杂的请求体结构
- 不同的认证要求

### 4. ecommerce_swagger.json
电商平台API的Swagger文档，包含：
- 商品管理接口 (GET/POST/PUT/DELETE /products)
- 购物车接口 (GET/POST /cart)
- 订单管理接口 (GET/POST /orders)

**特点：**
- 完整的电商业务场景
- 复杂的数据模型定义
- 多层嵌套的请求参数
- 枚举类型参数

## 使用示例

### 1. 使用主程序生成测试用例

```bash
# 从Markdown文档生成CSV格式测试用例
python main.py --ai-generate --input-doc data/examples/sample_api.md --output-format csv

# 从Swagger文档生成Excel格式测试用例
python main.py --ai-generate --input-doc data/examples/sample_api.json --output-format excel

# 指定输出目录
python main.py --ai-generate --input-doc data/examples/complex_api.md --output-format json --output-dir output/custom
```

### 2. 使用独立脚本生成测试用例

```bash
# 单文档处理
python ai_case_generator.py data/examples/sample_api.md --format csv

# 批量处理多个文档
python ai_case_generator.py data/examples/*.md --format excel --merge

# 预览模式
python ai_case_generator.py data/examples/complex_api.md --format json --preview

# 交互式模式
python ai_case_generator.py --interactive
```

### 3. 指定端点过滤

```bash
# 只处理登录相关接口
python ai_case_generator.py data/examples/sample_api.md --endpoints /login

# 处理多个指定端点
python main.py --ai-generate --input-doc data/examples/ecommerce_swagger.json --swagger-endpoint /products --swagger-endpoint /cart
```

## 生成结果示例

AI会为每个接口生成以下类型的测试用例：

1. **正向测试用例** (3个)
   - 基本正常场景
   - 完整参数场景
   - 最小参数场景

2. **反向测试用例** (2个)
   - 缺少必填参数
   - 参数类型错误
   - 参数值无效

3. **边界测试用例** (2个)
   - 字符串长度边界
   - 数值边界
   - 特殊字符

4. **结构验证用例** (1个)
   - JSON格式验证
   - 字段类型验证

5. **路径覆盖用例** (2个)
   - 不同路径参数
   - 查询参数组合

6. **权限验证用例** (如果需要认证)
   - 未认证访问
   - 无效token
   - 权限不足

## 配置说明

可以通过修改 `config/ai_config.ini` 来调整生成策略：

```ini
[generation]
positive_cases_count = 3    # 正向用例数量
negative_cases_count = 2    # 反向用例数量
boundary_cases_count = 2    # 边界用例数量
structure_cases_count = 1   # 结构用例数量
path_cases_count = 2        # 路径用例数量
include_auth_cases = true   # 是否包含认证用例
```

## 质量评分

生成的测试用例会经过质量验证，评分标准：
- A (90-100分): 优秀
- B (80-89分): 良好
- C (70-79分): 一般
- D (60-69分): 需要改进
- F (0-59分): 质量较差

评分考虑因素：
- 必填字段完整性
- URL和HTTP方法有效性
- JSON格式正确性
- 逻辑一致性
- 警告数量