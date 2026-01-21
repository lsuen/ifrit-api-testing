# ifrit-YAML数据驱动手册

## 一、YAML数据驱动概述

### 1.1 什么是YAML数据驱动
YAML（YAML Ain't Markup Language）是一种人类可读的数据序列化语言，广泛用于配置文件和数据交换。在ifrit框架中，YAML数据驱动允许您使用YAML格式定义API测试用例，提供比Excel和CSV更丰富的数据表达能力。

### 1.2 YAML的优势
- **可读性强**：语法简洁，层次清晰
- **结构化数据**：天然支持嵌套结构
- **注释支持**：可以添加注释说明
- **跨语言兼容**：广泛的语言支持

### 1.3 适用场景
- 复杂的API测试场景
- 需要嵌套数据结构的测试
- 需要详细注释说明的测试用例
- 与DevOps流程集成

## 二、YAML测试用例格式

### 2.1 基本格式
```yaml
# 测试用例集基本信息
suite_name: "用户管理API测试"
description: "测试用户管理相关API接口"
base_url: "http://api.example.com"

# 测试用例列表
test_cases:
  # 第一个测试用例
  - case_id: "TC_USER_001"
    case_name: "用户注册成功"
    method: "POST"
    url: "/api/users/register"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${token}"
    body:
      username: "testuser"
      email: "test@example.com"
      password: "secure_password"
    expected_status: 201
    expected_content: "success"
    variables:
      - name: "user_id"
        extractor: "jsonpath"
        expression: "$.data.id"
      - name: "auth_token"
        extractor: "regex"
        expression: '"token":"([^"]+)"'

  # 第二个测试用例
  - case_id: "TC_USER_002"
    case_name: "用户登录成功"
    method: "POST"
    url: "/api/users/login"
    headers:
      Content-Type: "application/json"
    body:
      username: "testuser"
      password: "secure_password"
    expected_status: 200
    json_path: "$.token"
    expected_json_value: "${regex:\"token\":\"([^\"]+)\"}"
```

### 2.2 数据类型支持
YAML支持多种数据类型：

#### 2.2.1 字符串类型
```yaml
# 普通字符串
simple_string: "hello world"
# 多行字符串
multiline_string: |
  这是第一行
  这是第二行
  这是第三行
# 内联字符串
inline_string: >
  这是一段很长的文本
  会被折叠成一行
```

#### 2.2.2 数字类型
```yaml
integer_value: 42
float_value: 3.14
scientific_notation: 1.23e+4
```

#### 2.2.3 布尔类型
```yaml
truth_value: true
false_value: false
```

#### 2.2.4 数组类型
```yaml
simple_array: [1, 2, 3, 4]
complex_array:
  - name: "item1"
    value: 100
  - name: "item2"
    value: 200
```

#### 2.2.5 对象类型
```yaml
nested_object:
  level1:
    level2:
      property: "deep_value"
  array_of_objects:
    - id: 1
      name: "first"
    - id: 2
      name: "second"
```

## 三、YAML测试用例详解

### 3.1 基础字段说明

#### 3.1.1 必需字段
- `case_id`: 测试用例唯一标识符
- `case_name`: 测试用例名称
- `method`: HTTP请求方法（GET、POST、PUT、DELETE等）
- `url`: 请求URL路径

#### 3.1.2 可选字段
- `headers`: 请求头信息
- `params`: URL参数
- `body`: 请求体内容
- `expected_status`: 期望的状态码
- `expected_content`: 期望的响应内容
- `json_path`: JSON路径表达式
- `expected_json_value`: 期望的JSON路径值
- `variables`: 变量提取规则

### 3.2 高级字段说明

#### 3.2.1 条件执行
```yaml
test_cases:
  - case_id: "CONDITIONAL_TEST"
    case_name: "条件执行测试"
    method: "GET"
    url: "/api/data"
    condition: "previous_case.success == true"  # 只有在前置条件满足时才执行
    expected_status: 200
```

#### 3.2.2 循环执行
```yaml
test_cases:
  - case_id: "LOOP_TEST"
    case_name: "循环执行测试"
    method: "POST"
    url: "/api/batch"
    loop:
      items: ["item1", "item2", "item3"]  # 循环数据
      variable: "current_item"  # 循环变量名
    body:
      name: "${current_item}"  # 使用循环变量
    expected_status: 200
```

#### 3.2.3 依赖关系
```yaml
test_cases:
  - case_id: "DEPENDENCY_PARENT"
    case_name: "依赖父测试"
    method: "POST"
    url: "/api/create"
    body:
      name: "test_resource"
    variables:
      - name: "resource_id"
        extractor: "jsonpath"
        expression: "$.id"
    expected_status: 201
  
  - case_id: "DEPENDENCY_CHILD"
    case_name: "依赖子测试"
    method: "GET"
    url: "/api/resources/${resource_id}"  # 依赖父测试的变量
    depends_on: "DEPENDENCY_PARENT"  # 明确声明依赖关系
    expected_status: 200
```

## 四、变量提取与使用

### 4.1 变量提取方法

#### 4.1.1 JSONPath提取
```yaml
test_cases:
  - case_id: "JSONPATH_EXTRACT"
    case_name: "JSONPath提取测试"
    method: "GET"
    url: "/api/user/profile"
    variables:
      - name: "user_id"
        extractor: "jsonpath"
        expression: "$.id"
      - name: "user_email"
        extractor: "jsonpath"
        expression: "$.profile.email"
    expected_status: 200
```

#### 4.1.2 正则表达式提取
```yaml
test_cases:
  - case_id: "REGEX_EXTRACT"
    case_name: "正则表达式提取测试"
    method: "GET"
    url: "/api/token"
    variables:
      - name: "access_token"
        extractor: "regex"
        expression: '"access_token":"([^"]+)"'
      - name: "refresh_token"
        extractor: "regex" 
        expression: '"refresh_token":"([^"]+)"'
    expected_status: 200
```

#### 4.1.3 XPath提取（如支持XML响应）
```yaml
test_cases:
  - case_id: "XPATH_EXTRACT"
    case_name: "XPath提取测试"
    method: "GET"
    url: "/api/data.xml"
    variables:
      - name: "data_value"
        extractor: "xpath"
        expression: "//data/value/text()"
    expected_status: 200
```

### 4.2 变量使用
在后续测试用例中使用提取的变量：

```yaml
test_cases:
  # 第一个用例提取变量
  - case_id: "EXTRACT_VAR"
    case_name: "提取变量"
    method: "POST"
    url: "/api/create"
    body:
      name: "test_object"
    variables:
      - name: "object_id"
        extractor: "jsonpath"
        expression: "$.id"
    expected_status: 201
  
  # 第二个用例使用变量
  - case_id: "USE_VAR"
    case_name: "使用变量"
    method: "PUT"
    url: "/api/update/${object_id}"  # 使用提取的变量
    body:
      id: "${object_id}"  # 在请求体中使用变量
      status: "active"
    expected_status: 200
```

## 五、YAML文件组织结构

### 5.1 单文件多用例
适合小型测试套件：
```yaml
suite_name: "简单API测试"
description: "基本的API功能测试"
base_url: "http://localhost:8080"

test_cases:
  - case_id: "TC001"
    case_name: "测试用例1"
    # ... 用例详情
  - case_id: "TC002"
    case_name: "测试用例2"
    # ... 用例详情
```

### 5.2 多文件组织
适合大型测试套件：

#### 5.2.1 按功能模块组织
```
data/yaml_data/
├── user_management.yaml
├── product_catalog.yaml
├── order_processing.yaml
└── authentication.yaml
```

#### 5.2.2 按测试类型组织
```
data/yaml_data/
├── smoke_tests/
│   ├── login_smoke.yaml
│   └── purchase_smoke.yaml
├── regression_tests/
│   ├── user_regression.yaml
│   └── product_regression.yaml
└── integration_tests/
    ├── api_integration.yaml
    └── service_integration.yaml
```

### 5.3 配置继承
可以使用YAML锚点实现配置继承：

```yaml
# 定义公共配置
common_headers: &common_headers
  Content-Type: "application/json"
  Accept: "application/json"

common_settings: &common_settings
  headers: 
    <<: *common_headers
  expected_status: 200

# 使用公共配置
test_cases:
  - case_id: "INHERITED_TEST"
    case_name: "继承配置测试"
    method: "GET"
    url: "/api/data"
    <<: *common_settings  # 继承公共设置
```

## 六、实际应用示例

### 6.1 用户管理API测试
```yaml
suite_name: "用户管理API测试"
description: "全面测试用户管理相关功能"
base_url: "http://api.example.com"

test_cases:
  # 用户注册
  - case_id: "USER_REGISTER"
    case_name: "用户注册"
    method: "POST"
    url: "/api/auth/register"
    headers:
      Content-Type: "application/json"
    body:
      username: "newuser${random_int}"
      email: "newuser${random_int}@example.com"
      password: "SecurePassword123!"
      confirm_password: "SecurePassword123!"
    expected_status: 201
    variables:
      - name: "user_id"
        extractor: "jsonpath"
        expression: "$.data.id"
      - name: "verification_token"
        extractor: "jsonpath"
        expression: "$.data.verification_token"
  
  # 邮箱验证
  - case_id: "EMAIL_VERIFY"
    case_name: "邮箱验证"
    method: "POST"
    url: "/api/auth/verify-email"
    headers:
      Content-Type: "application/json"
    body:
      token: "${verification_token}"
    expected_status: 200
  
  # 用户登录
  - case_id: "USER_LOGIN"
    case_name: "用户登录"
    method: "POST"
    url: "/api/auth/login"
    headers:
      Content-Type: "application/json"
    body:
      username: "newuser${random_int}"
      password: "SecurePassword123!"
    expected_status: 200
    variables:
      - name: "access_token"
        extractor: "jsonpath"
        expression: "$.data.access_token"
      - name: "refresh_token"
        extractor: "jsonpath"
        expression: "$.data.refresh_token"
  
  # 获取用户信息
  - case_id: "GET_PROFILE"
    case_name: "获取用户资料"
    method: "GET"
    url: "/api/users/profile"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer ${access_token}"
    expected_status: 200
    json_path: "$.id"
    expected_json_value: "${user_id}"
```

### 6.2 产品搜索API测试
```yaml
suite_name: "产品搜索API测试"
description: "测试产品搜索相关功能"
base_url: "http://api.example.com"

test_cases:
  # 搜索产品
  - case_id: "SEARCH_PRODUCTS"
    case_name: "搜索产品"
    method: "GET"
    url: "/api/products/search"
    params:
      q: "laptop"
      category: "electronics"
      min_price: 100
      max_price: 1000
      page: 1
      size: 10
    headers:
      Content-Type: "application/json"
    expected_status: 200
    json_path: "$.total"
    expected_json_value: "${gt:0}"  # 验证总数大于0
  
  # 获取搜索结果详情
  - case_id: "GET_PRODUCT_DETAIL"
    case_name: "获取产品详情"
    method: "GET"
    url: "/api/products/${jsonpath:$.products[0].id}"  # 使用搜索结果的第一个产品ID
    headers:
      Content-Type: "application/json"
    expected_status: 200
```

## 七、运行YAML测试

### 7.1 命令行运行
目前框架可能还不直接支持YAML格式，如果需要添加支持，可以按以下步骤操作：

#### 7.1.1 添加YAML解析器
创建YAML解析器文件：
```python
# utils/yaml_handler.py
import yaml
import json

class YamlHandler:
    def load_test_cases(self, yaml_file_path):
        """从YAML文件加载测试用例"""
        with open(yaml_file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data.get('test_cases', [])
    
    def convert_to_internal_format(self, yaml_test_cases):
        """将YAML格式转换为框架内部格式"""
        internal_cases = []
        for case in yaml_test_cases:
            # 转换逻辑...
            internal_cases.append(case)
        return internal_cases
```

#### 7.1.2 创建YAML测试驱动
```python
# drivers/test_api_yaml_driver.py
import pytest
from utils.yaml_handler import YamlHandler
from core.test_executor import TestExecutor

class TestAPIYAML:
    @pytest.fixture(scope="class")
    def test_cases(self):
        """读取YAML测试用例"""
        yaml_handler = YamlHandler()
        yaml_cases = yaml_handler.load_test_cases("data/yaml_data/test_cases.yaml")
        return yaml_handler.convert_to_internal_format(yaml_cases)
    
    @pytest.mark.parametrize("test_case", test_cases)
    def test_api_case(self, test_case):
        """执行单个测试用例"""
        executor = TestExecutor()
        executor.execute_test_case(test_case)
```

### 7.2 配置文件设置
在[test_data_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/test_data_config.ini)中添加YAML支持：
```ini
[yaml]
# YAML测试数据配置
yaml_data_dir = data/yaml_data
default_file_encoding = utf-8
enable_variable_extraction = true
```

## 八、最佳实践

### 8.1 文件命名规范
- 使用描述性的文件名
- 按功能或模块组织文件
- 使用一致的命名约定

### 8.2 用例设计原则
- 保持测试用例独立性
- 使用有意义的case_id和case_name
- 合理使用变量传递数据
- 添加适当的注释说明

### 8.3 数据管理
- 将测试数据与测试逻辑分离
- 使用环境配置管理不同环境的数据
- 避免在测试用例中硬编码敏感信息

### 8.4 版本控制
- 将YAML文件纳入版本控制
- 使用分支管理不同版本的测试用例
- 定期备份重要的测试数据

## 九、常见问题及解决方案

### 9.1 YAML语法错误
**问题**：YAML解析失败
**解决方案**：
- 检查缩进是否正确（使用空格，不是Tab）
- 验证冒号后是否有空格
- 确认引号使用正确

### 9.2 变量引用失败
**问题**：变量无法正确替换
**解决方案**：
- 确认变量提取步骤已成功执行
- 检查变量名拼写是否正确
- 验证变量作用域

### 9.3 嵌套数据处理
**问题**：处理复杂的嵌套数据结构困难
**解决方案**：
- 使用JSONPath表达式精确提取数据
- 分解复杂用例为多个简单用例
- 利用YAML的锚点和别名功能

通过本手册，您可以充分利用YAML格式的强大功能来组织和管理API测试用例，提高测试效率和维护性。