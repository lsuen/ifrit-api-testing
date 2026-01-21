# ifrit-二次开发详细手册

## 一、框架架构概览

### 1.1 整体架构
ifrit框架采用模块化设计，主要分为以下几个层次：
- **核心层**：提供基础功能（请求处理、断言、数据处理等）
- **业务层**：实现具体业务逻辑（测试执行、报告生成等）
- **接口层**：提供命令行接口和外部调用接口
- **数据层**：处理各种数据格式和数据源

### 1.2 主要模块关系
```
[main.py] -> [CLIManager] -> [TestRunner/ReportManager/AIGenerator]
     |                           |
     v                           v
[config.py] <- [EnvConfig]  [TestExecutor] -> [RequestHandler/AssertHandler/DataHandler]
```

## 二、模块详解

### 2.1 核心模块（core/目录）

#### 2.1.1 request_handler.py - 请求处理器
这是处理HTTP请求的核心模块，负责：
- 发送HTTP请求（GET、POST、PUT、DELETE等）
- 处理请求头、请求体
- 处理响应结果

**扩展方法**：
如果你想添加新的HTTP认证方式，可以在RequestHandler类中添加相应的方法：
```python
def add_custom_auth(self, auth_type, credentials):
    """添加自定义认证方式"""
    if auth_type == 'custom_token':
        self.session.headers.update({'X-Custom-Token': credentials})
    # 添加其他认证方式...
```

#### 2.1.2 assert_handler.py - 断言处理器
负责处理各种类型的断言，包括：
- 状态码断言
- 响应内容断言
- JSON路径断言
- 正则表达式断言

**扩展方法**：
要添加新的断言类型，可以继承AssertHandler类并重写assert_response方法：
```python
class CustomAssertHandler(AssertHandler):
    def assert_custom_format(self, actual_value, expected_format):
        """添加自定义格式断言"""
        # 实现自定义格式验证逻辑
        pass
```

#### 2.1.3 data_handler.py - 数据处理器
负责处理测试过程中的数据：
- 变量提取和存储
- 数据关联
- 正则表达式处理

**扩展方法**：
要添加新的数据提取方式，可以在DataHandler类中添加新方法：
```python
def extract_by_xpath(self, response_text, xpath_expression):
    """添加XPath数据提取支持"""
    # 实现XPath解析逻辑
    pass
```

#### 2.1.4 cli_manager.py - 命令行接口管理器
处理所有命令行参数解析和分发。

**扩展方法**：
要添加新的命令行参数，在`_create_parser`方法中添加：
```python
parser.add_argument(
    "--new-feature",
    action="store_true",
    help="新增功能说明"
)
```

### 2.2 配置模块（config/目录）

#### 2.2.1 config.py - 全局配置管理
管理所有配置项，包括环境配置、测试数据配置等。

**扩展方法**：
要添加新的配置项，可以在Config类中添加：
```python
def get_custom_setting(self):
    """获取自定义设置"""
    return self.env_config.get('custom_section', 'setting_name', fallback='default_value')
```

### 2.3 驱动模块（drivers/目录）

#### 2.3.1 测试驱动文件
每个测试驱动文件负责处理特定格式的测试数据，如：
- test_api_excel_driver.py - 处理Excel格式测试数据
- test_api_csv_driver.py - 处理CSV格式测试数据
- test_api_json_driver.py - 处理JSON格式测试数据

**添加新驱动方法**：
1. 创建新的驱动文件，如`test_api_yaml_driver.py`
2. 继承通用测试执行逻辑
3. 实现特定格式的数据读取方法

## 三、功能扩展实战

### 3.1 添加新的数据格式支持

假设我们要添加YAML格式支持：

#### 3.1.1 创建YAML数据处理器
在[utils/test_case_reader.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/utils/test_case_reader.py)中添加YAML支持：
```python
import yaml

class DataHandler:
    def read_yaml_test_cases(self, file_path):
        """读取YAML格式的测试用例"""
        with open(file_path, 'r', encoding='utf-8') as file:
            test_cases = yaml.safe_load(file)
        return test_cases
```

#### 3.1.2 创建YAML测试驱动
创建[drivers/test_api_yaml_driver.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/drivers/test_api_yaml_driver.py)：
```python
import pytest
from utils.test_case_reader import DataHandler
from core.test_executor import TestExecutor

class TestAPIYAML:
    @pytest.fixture(scope="class")
    def test_cases(self):
        """读取YAML测试用例"""
        data_handler = DataHandler()
        return data_handler.read_yaml_test_cases("data/yaml_data/test_cases.yaml")
    
    @pytest.mark.parametrize("test_case", test_cases)
    def test_api_case(self, test_case):
        """执行单个测试用例"""
        executor = TestExecutor()
        executor.execute_test_case(test_case)
```

#### 3.1.3 更新命令行接口
在[core/cli_manager.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/cli_manager.py)中添加YAML选项：
```python
parser.add_argument(
    "--type",
    choices=["excel", "csv", "json", "yaml", "all"],
    help="指定测试类型: excel/csv/json/yaml/all"
)
```

#### 3.1.4 更新测试运行器
在[core/test_runner.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/test_runner.py)中添加YAML处理逻辑：
```python
elif test_type == "yaml":
    cmd.insert(1, "drivers/test_api_yaml_driver.py")
    self.logger.info("运行YAML测试用例")
```

### 3.2 添加新的断言类型

#### 3.2.1 实现Schema验证断言
在[core/assert_handler.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/assert_handler.py)中添加：
```python
import jsonschema

def assert_json_schema(self, response_json, schema):
    """验证响应JSON是否符合指定Schema"""
    try:
        jsonschema.validate(instance=response_json, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        self.logger.error(f"JSON Schema验证失败: {e.message}")
        return False
```

### 3.3 添加数据库支持

#### 3.3.1 创建数据库连接管理器
在[core/database_handler.py](file:///C:/CodeFiles/PyProjects/ifrit-apitest/core/database_handler.py)（新文件）中：
```python
import sqlite3
import psycopg2
import pymysql

class DatabaseHandler:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
    
    def connect(self):
        """根据配置建立数据库连接"""
        db_type = self.db_config.get('type', 'sqlite')
        if db_type == 'sqlite':
            self.connection = sqlite3.connect(self.db_config['path'])
        elif db_type == 'postgresql':
            self.connection = psycopg2.connect(**self.db_config)
        elif db_type == 'mysql':
            self.connection = pymysql.connect(**self.db_config)
    
    def execute_query(self, query, params=None):
        """执行查询并返回结果"""
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
```

## 四、插件机制

### 4.1 插件架构设计
框架支持插件机制，允许动态扩展功能而不需要修改核心代码。

### 4.2 创建插件
创建插件的基本步骤：
1. 创建插件目录：`plugins/`
2. 编写插件类，继承基础接口
3. 在配置中注册插件

### 4.3 示例：创建报告插件
```python
# plugins/custom_report_plugin.py
class CustomReportPlugin:
    def __init__(self, config):
        self.config = config
    
    def generate_report(self, test_results):
        """生成自定义格式报告"""
        # 实现自定义报告逻辑
        pass
    
    def export_report(self, report_data, output_path):
        """导出报告到指定路径"""
        # 实现报告导出逻辑
        pass
```

## 五、最佳实践

### 5.1 代码规范
- 遵循PEP 8代码风格
- 使用有意义的变量名和函数名
- 添加适当的注释和文档字符串
- 保持函数简洁，单一职责原则

### 5.2 测试原则
- 为新增功能编写单元测试
- 保持高代码覆盖率
- 使用mock对象隔离外部依赖

### 5.3 性能考虑
- 避免不必要的重复计算
- 合理使用缓存机制
- 注意内存使用情况

### 5.4 安全性
- 验证所有外部输入
- 避免在日志中记录敏感信息
- 使用安全的依赖库版本

## 六、调试技巧

### 6.1 日志调试
使用框架内置的日志系统：
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 6.2 单元测试
在[__internal_tests/](file:///C:/CodeFiles/PyProjects/ifrit-apitest/__internal_tests)目录下编写单元测试：
```python
import unittest
from core.request_handler import RequestHandler

class TestRequestHandler(unittest.TestCase):
    def test_get_request(self):
        """测试GET请求功能"""
        handler = RequestHandler()
        response = handler.send_request('GET', 'http://example.com')
        self.assertEqual(response.status_code, 200)
```

### 6.3 集成测试
编写集成测试验证模块间的协作：
```python
def test_end_to_end_flow():
    """测试端到端流程"""
    # 创建测试数据
    # 执行测试流程
    # 验证结果
```

## 七、常见问题及解决方案

### 7.1 模块导入问题
**问题**：出现ImportError错误
**解决方案**：
- 检查模块路径是否正确
- 确认__init__.py文件存在
- 检查Python环境是否正确激活

### 7.2 配置文件问题
**问题**：配置无法正确加载
**解决方案**：
- 验证配置文件格式（INI、JSON、YAML）
- 检查配置项名称拼写
- 确认配置文件路径正确

### 7.3 扩展功能不生效
**问题**：新增功能无法正常工作
**解决方案**：
- 检查是否正确更新了命令行接口
- 确认新模块是否正确注册
- 验证依赖关系是否完整

## 八、版本升级指南

### 8.1 向后兼容性
在进行框架升级时，注意保持向后兼容性：
- 不要删除现有API
- 如需修改API，提供迁移指南
- 保留旧版本功能一段时间

### 8.2 升级步骤
1. 备份现有代码
2. 在测试环境中验证新版本
3. 逐步迁移到生产环境
4. 监控升级后的运行状态

## 九、贡献指南

### 9.1 代码贡献流程
1. Fork项目仓库
2. 创建功能分支
3. 实现功能并添加测试
4. 提交代码审查
5. 合并到主分支

### 9.2 文档更新
- 更新相关文档
- 添加使用示例
- 提供配置说明

通过本手册，您可以深入了解ifrit框架的架构设计，掌握扩展功能的方法，并能够根据具体需求进行定制开发。