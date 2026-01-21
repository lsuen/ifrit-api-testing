# ifrit-数据库数据驱动手册

## 一、数据库数据驱动概述

### 1.1 什么是数据库数据驱动
数据库数据驱动是一种测试方法，它将测试数据存储在数据库中，测试执行时动态从数据库读取测试数据。这种方法特别适用于需要大量测试数据、复杂数据关系或实时数据验证的场景。

### 1.2 数据库数据驱动的优势
- **数据容量大**：可以存储大量的测试数据
- **数据关系清晰**：利用数据库的表关系表示复杂的测试数据结构
- **数据一致性**：保证测试数据的一致性和完整性
- **实时性**：可以使用真实环境的数据库进行测试
- **易于管理**：通过SQL查询灵活筛选测试数据
- **数据复用**：多套测试可以共享同一数据源

### 1.3 适用场景
- 需要大量测试数据的场景
- 测试数据之间存在复杂关联关系
- 需要验证数据库操作的场景
- 与现有数据库系统集成的测试
- 需要定期更新测试数据的长期项目

## 二、数据库连接配置

### 2.1 数据库支持类型
ifrit框架支持多种数据库类型：
- SQLite（轻量级，适合本地测试）
- MySQL（广泛应用的关系型数据库）
- PostgreSQL（功能强大的开源数据库）
- SQL Server（企业级数据库）
- Oracle（企业级数据库）
- MongoDB（文档型数据库，需要额外配置）

### 2.2 配置数据库连接

#### 2.2.1 配置文件设置
在[config/env_config.ini](file:///C:/CodeFiles/PyProjects/ifrit-apitest/config/env_config.ini)中添加数据库配置：

```ini
[database]
# 数据库类型
type = mysql
# 主机地址
host = localhost
# 端口号
port = 3306
# 数据库名称
database = test_db
# 用户名
username = test_user
# 密码
password = test_password
# 连接池大小
pool_size = 10
# 连接超时时间（秒）
timeout = 30

# 可选：其他数据库配置示例
[sqlite_db]
type = sqlite
path = ./data/test.db
timeout = 30

[postgres_db]
type = postgresql
host = localhost
port = 5432
database = test_db
username = test_user
password = test_password
ssl_mode = disable
```

#### 2.2.2 环境变量配置（推荐用于敏感信息）
为了安全起见，建议将敏感信息（如密码）存储在环境变量中：

```bash
# Windows
set DB_PASSWORD=your_secure_password

# Linux/Mac
export DB_PASSWORD=your_secure_password
```

然后在配置文件中引用：
```ini
[database]
# ... 其他配置
password = ${env:DB_PASSWORD}
```

### 2.3 数据库连接管理

#### 2.3.1 连接池配置
为了提高性能，建议使用连接池：

```ini
[database_pool]
min_connections = 5
max_connections = 20
idle_timeout = 300
connection_timeout = 30
```

## 三、数据库测试数据设计

### 3.1 测试数据表结构设计

#### 3.1.1 基础测试用例表
```sql
CREATE TABLE test_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    case_name VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    url VARCHAR(500) NOT NULL,
    headers TEXT,
    params TEXT,
    body TEXT,
    expected_status INT,
    expected_content TEXT,
    json_path VARCHAR(200),
    expected_json_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 3.1.2 测试数据参数表
```sql
CREATE TABLE test_parameters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(50) NOT NULL,
    param_name VARCHAR(100) NOT NULL,
    param_value TEXT,
    param_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    FOREIGN KEY (case_id) REFERENCES test_cases(case_id)
);
```

#### 3.1.3 测试结果记录表
```sql
CREATE TABLE test_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(50) NOT NULL,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pass', 'fail', 'skip') NOT NULL,
    response_time_ms INT,
    actual_status INT,
    actual_content TEXT,
    error_message TEXT,
    execution_environment VARCHAR(50)
);
```

### 3.2 数据关系设计

#### 3.2.1 测试用例依赖关系
```sql
CREATE TABLE test_case_dependencies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    parent_case_id VARCHAR(50) NOT NULL,
    child_case_id VARCHAR(50) NOT NULL,
    dependency_type ENUM('sequential', 'parallel', 'conditional') DEFAULT 'sequential',
    FOREIGN KEY (parent_case_id) REFERENCES test_cases(case_id),
    FOREIGN KEY (child_case_id) REFERENCES test_cases(case_id)
);
```

#### 3.2.2 测试数据关联表
```sql
CREATE TABLE test_data_relations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    source_table VARCHAR(100) NOT NULL,
    source_record_id VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_record_id VARCHAR(100) NOT NULL,
    relation_type VARCHAR(50) NOT NULL
);
```

## 四、数据库操作实现

### 4.1 数据库连接类实现

#### 4.1.1 基础数据库连接类
```python
# core/database_handler.py
import sqlite3
import pymysql
import psycopg2
import json
from abc import ABC, abstractmethod
from contextlib import contextmanager

class DatabaseConnection(ABC):
    """数据库连接抽象基类"""
    
    @abstractmethod
    def connect(self):
        """建立数据库连接"""
        pass
    
    @abstractmethod
    def execute_query(self, query, params=None):
        """执行查询"""
        pass
    
    @abstractmethod
    def execute_update(self, query, params=None):
        """执行更新操作"""
        pass

class MySQLConnection(DatabaseConnection):
    """MySQL数据库连接实现"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        """建立MySQL连接"""
        self.connection = pymysql.connect(
            host=self.config['host'],
            port=int(self.config['port']),
            user=self.config['username'],
            password=self.config['password'],
            database=self.config['database'],
            charset='utf8mb4',
            autocommit=False
        )
        return self.connection
    
    def execute_query(self, query, params=None):
        """执行查询操作"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        self.connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows

class SQLiteConnection(DatabaseConnection):
    """SQLite数据库连接实现"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        """建立SQLite连接"""
        self.connection = sqlite3.connect(self.config['path'])
        self.connection.row_factory = sqlite3.Row  # 返回字典形式的结果
        return self.connection
    
    def execute_query(self, query, params=None):
        """执行查询操作"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params or () if params else ())
        result = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return result
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params or () if params else ())
        self.connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        return affected_rows
```

### 4.2 测试数据读取器

#### 4.2.1 数据库测试数据读取器
```python
# utils/database_test_case_reader.py
from core.database_handler import MySQLConnection, SQLiteConnection
from config.config import Config
import json

class DatabaseTestCaseReader:
    """从数据库读取测试用例的类"""
    
    def __init__(self):
        self.config = Config()
        self.db_connection = self._create_connection()
    
    def _create_connection(self):
        """根据配置创建数据库连接"""
        db_config = self.config.get_database_config()
        db_type = db_config.get('type', 'sqlite')
        
        if db_type == 'mysql':
            return MySQLConnection(db_config)
        elif db_type == 'sqlite':
            return SQLiteConnection(db_config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def get_test_cases(self, query_conditions=None):
        """从数据库获取测试用例"""
        base_query = """
        SELECT 
            case_id,
            case_name,
            method,
            url,
            headers,
            params,
            body,
            expected_status,
            expected_content,
            json_path,
            expected_json_value
        FROM test_cases 
        WHERE is_active = TRUE
        """
        
        params = []
        if query_conditions:
            where_clause, params = self._build_where_clause(query_conditions)
            base_query += f" AND {where_clause}"
        
        base_query += " ORDER BY id"
        
        raw_cases = self.db_connection.execute_query(base_query, params)
        
        # 处理JSON字段
        processed_cases = []
        for case in raw_cases:
            processed_case = dict(case)
            
            # 解析JSON字段
            if processed_case.get('headers'):
                processed_case['headers'] = json.loads(processed_case['headers'])
            if processed_case.get('params'):
                processed_case['params'] = json.loads(processed_case['params']) if processed_case['params'] else {}
            if processed_case.get('body'):
                processed_case['body'] = json.loads(processed_case['body']) if processed_case['body'] else {}
            
            processed_cases.append(processed_case)
        
        return processed_cases
    
    def _build_where_clause(self, conditions):
        """构建WHERE子句"""
        clauses = []
        params = []
        
        for key, value in conditions.items():
            if isinstance(value, list):
                placeholders = ','.join(['%s'] * len(value))
                clauses.append(f"{key} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{key} = %s")
                params.append(value)
        
        return ' AND '.join(clauses), params
    
    def get_test_parameters(self, case_id):
        """获取测试参数"""
        query = "SELECT param_name, param_value, param_type FROM test_parameters WHERE case_id = %s"
        params = self.db_connection.execute_query(query, [case_id])
        
        # 转换参数类型
        converted_params = {}
        for param in params:
            value = param['param_value']
            param_type = param['param_type']
            
            if param_type == 'number':
                converted_params[param['param_name']] = float(value) if '.' in str(value) else int(value)
            elif param_type == 'boolean':
                converted_params[param['param_name']] = value.lower() in ('true', '1', 'yes')
            elif param_type == 'json':
                converted_params[param['param_name']] = json.loads(value)
            else:
                converted_params[param['param_name']] = value
        
        return converted_params
```

### 4.3 数据库测试驱动

#### 4.3.1 创建数据库测试驱动
```python
# drivers/test_api_database_driver.py
import pytest
from utils.database_test_case_reader import DatabaseTestCaseReader
from core.test_executor import TestExecutor

class TestAPIDatabase:
    """数据库驱动的API测试类"""
    
    @pytest.fixture(scope="class")
    def test_cases(self):
        """从数据库读取测试用例"""
        reader = DatabaseTestCaseReader()
        
        # 可以根据需要添加查询条件
        conditions = {
            'is_active': True
            # 'execution_environment': 'production'  # 只运行生产环境的测试
        }
        
        return reader.get_test_cases(conditions)
    
    @pytest.mark.parametrize("test_case", test_cases)
    def test_api_case(self, test_case):
        """执行单个测试用例"""
        # 获取测试参数并合并到测试用例中
        parameters = DatabaseTestCaseReader().get_test_parameters(test_case['case_id'])
        
        # 合并参数到测试用例
        if parameters:
            # 如果body是字典，合并参数
            if isinstance(test_case.get('body'), dict):
                test_case['body'].update(parameters)
            # 如果params是字典，合并参数
            if isinstance(test_case.get('params'), dict):
                test_case['params'].update(parameters)
        
        executor = TestExecutor()
        executor.execute_test_case(test_case)
```

## 五、数据库测试用例管理

### 5.1 测试用例生命周期管理

#### 5.1.1 测试用例状态管理
```sql
-- 添加测试用例状态字段
ALTER TABLE test_cases ADD COLUMN status ENUM('draft', 'review', 'approved', 'deprecated') DEFAULT 'draft';
ALTER TABLE test_cases ADD COLUMN priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium';
ALTER TABLE test_cases ADD COLUMN tags VARCHAR(500); -- 用逗号分隔的标签
```

#### 5.1.2 测试用例版本管理
```sql
CREATE TABLE test_case_versions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(50) NOT NULL,
    version_number INT NOT NULL,
    version_data JSON NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (case_id) REFERENCES test_cases(case_id)
);
```

### 5.2 测试数据准备

#### 5.2.1 测试数据初始化
```python
# utils/test_data_initializer.py
class TestDataInitializer:
    """测试数据初始化工具"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
    
    def prepare_test_data(self, scenario_name):
        """为特定场景准备测试数据"""
        # 清理旧数据
        self.cleanup_test_data(scenario_name)
        
        # 插入测试数据
        self.insert_scenario_data(scenario_name)
    
    def cleanup_test_data(self, scenario_name):
        """清理测试数据"""
        # 删除测试相关的数据
        cleanup_queries = [
            f"DELETE FROM test_users WHERE scenario = '{scenario_name}'",
            f"DELETE FROM test_orders WHERE scenario = '{scenario_name}'"
        ]
        
        for query in cleanup_queries:
            self.db_connection.execute_update(query)
    
    def insert_scenario_data(self, scenario_name):
        """插入场景特定的测试数据"""
        # 根据场景名称插入相应的测试数据
        if scenario_name == 'user_registration':
            self._insert_user_registration_data()
        elif scenario_name == 'product_purchase':
            self._insert_product_purchase_data()
    
    def _insert_user_registration_data(self):
        """插入用户注册场景的测试数据"""
        # 插入测试用户数据
        query = """
        INSERT INTO test_users (username, email, scenario, created_at) 
        VALUES (%s, %s, %s, NOW())
        """
        self.db_connection.execute_update(query, [
            f'test_user_{int(time.time())}',
            f'test_user_{int(time.time())}@example.com',
            'user_registration'
        ])
```

## 六、数据库测试结果管理

### 6.1 测试结果记录

#### 6.1.1 结果记录表设计
```sql
CREATE TABLE test_execution_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    execution_id VARCHAR(100) NOT NULL,
    case_id VARCHAR(50) NOT NULL,
    execution_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_end TIMESTAMP NULL,
    duration_ms INT,
    status ENUM('pass', 'fail', 'skip', 'error') NOT NULL,
    actual_response LONGTEXT,
    actual_status_code INT,
    error_details TEXT,
    execution_environment VARCHAR(50),
    executed_by VARCHAR(100),
    tags VARCHAR(500),
    INDEX idx_case_id (case_id),
    INDEX idx_execution_id (execution_id),
    INDEX idx_status (status),
    INDEX idx_execution_start (execution_start)
);
```

### 6.2 结果分析

#### 6.2.1 测试结果分析查询
```sql
-- 获取测试执行统计
SELECT 
    status,
    COUNT(*) as count,
    AVG(duration_ms) as avg_duration,
    MIN(duration_ms) as min_duration,
    MAX(duration_ms) as max_duration
FROM test_execution_history 
WHERE execution_start >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY status;

-- 获取失败的测试用例
SELECT 
    t.case_name,
    h.error_details,
    h.execution_start
FROM test_cases t
JOIN test_execution_history h ON t.case_id = h.case_id
WHERE h.status = 'fail' 
AND h.execution_start >= DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY h.execution_start DESC;
```

## 七、实际应用示例

### 7.1 电商API测试数据示例

#### 7.1.1 插入测试数据
```sql
-- 插入产品数据
INSERT INTO test_cases (case_id, case_name, method, url, headers, body, expected_status) VALUES
('ECOMMERCE_001', '获取产品列表', 'GET', '/api/products', '{"Content-Type": "application/json"}', NULL, 200),
('ECOMMERCE_002', '搜索产品', 'GET', '/api/products/search?q=laptop', '{"Content-Type": "application/json"}', NULL, 200),
('ECOMMERCE_003', '获取产品详情', 'GET', '/api/products/{product_id}', '{"Content-Type": "application/json"}', NULL, 200),
('ECOMMERCE_004', '添加产品到购物车', 'POST', '/api/cart/add', '{"Content-Type": "application/json"}', '{"product_id": 123, "quantity": 2}', 200);

-- 插入测试参数
INSERT INTO test_parameters (case_id, param_name, param_value, param_type) VALUES
('ECOMMERCE_002', 'limit', '10', 'number'),
('ECOMMERCE_002', 'offset', '0', 'number');
```

#### 7.1.2 运行数据库驱动的测试
```bash
# 运行数据库驱动的测试（假设已实现）
python main.py --type database --db-config production
```

### 7.2 用户认证API测试示例

#### 7.2.1 认证相关测试数据
```sql
-- 插入认证相关的测试用例
INSERT INTO test_cases (case_id, case_name, method, url, headers, body, expected_status) VALUES
('AUTH_001', '用户注册', 'POST', '/api/auth/register', '{"Content-Type": "application/json"}', '{"username": "${test_username}", "email": "${test_email}", "password": "${test_password}"}', 201),
('AUTH_002', '用户登录', 'POST', '/api/auth/login', '{"Content-Type": "application/json"}', '{"username": "${test_username}", "password": "${test_password}"}', 200),
('AUTH_003', '获取用户信息', 'GET', '/api/users/me', '{"Content-Type": "application/json", "Authorization": "Bearer ${auth_token}"}', NULL, 200);

-- 插入测试参数
INSERT INTO test_parameters (case_id, param_name, param_value, param_type) VALUES
('AUTH_001', 'test_username', 'testuser_${timestamp}', 'string'),
('AUTH_001', 'test_email', 'test_${timestamp}@example.com', 'string'),
('AUTH_001', 'test_password', 'SecurePassword123!', 'string');
```

## 八、性能优化

### 8.1 查询优化

#### 8.1.1 索引优化
```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_test_cases_active_status ON test_cases(is_active, status);
CREATE INDEX idx_test_execution_case_time ON test_execution_history(case_id, execution_start);
CREATE INDEX idx_test_cases_priority ON test_cases(priority);
```

### 8.2 连接池优化
```ini
[database_pool_optimized]
min_connections = 2
max_connections = 10
idle_timeout = 600
connection_timeout = 10
max_overflow = 5
pool_recycle = 3600
```

### 8.3 批量操作
```python
def execute_batch_queries(self, queries_with_params):
    """批量执行查询以提高性能"""
    if not self.connection:
        self.connect()
    
    cursor = self.connection.cursor()
    try:
        for query, params in queries_with_params:
            cursor.execute(query, params)
        self.connection.commit()
    except Exception as e:
        self.connection.rollback()
        raise e
    finally:
        cursor.close()
```

## 九、安全考虑

### 9.1 SQL注入防护
- 使用参数化查询
- 验证输入数据
- 使用ORM框架（如果可能）

### 9.2 敏感数据保护
- 不在数据库中存储明文密码
- 使用加密连接
- 限制数据库用户权限

### 9.3 访问控制
- 为测试数据库创建专用账户
- 限制账户权限（只读或特定表权限）
- 定期轮换数据库密码

## 十、最佳实践

### 10.1 数据库设计最佳实践
- 使用适当的数据类型
- 合理设计索引
- 规范化数据结构
- 使用外键约束保证数据完整性

### 10.2 测试数据管理最佳实践
- 保持测试数据的独立性
- 使用数据标记区分不同测试环境
- 定期清理过期测试数据
- 备份重要测试数据

### 10.3 性能最佳实践
- 避免N+1查询问题
- 使用连接池
- 合理设置超时时间
- 监控数据库性能

### 10.4 维护最佳实践
- 版本控制数据库模式变更
- 记录数据库变更历史
- 定期备份数据库
- 监控数据库健康状况

## 十一、常见问题及解决方案

### 11.1 连接问题
**问题**：无法连接到数据库
**解决方案**：
- 检查数据库服务是否运行
- 验证连接参数是否正确
- 检查防火墙设置
- 确认数据库用户权限

### 11.2 查询性能问题
**问题**：查询速度慢
**解决方案**：
- 检查并优化SQL查询
- 添加适当索引
- 考虑查询缓存
- 分析慢查询日志

### 11.3 数据一致性问题
**问题**：测试数据不一致
**解决方案**：
- 使用事务确保数据一致性
- 实现适当的锁机制
- 验证数据完整性约束

通过本手册，您可以有效地利用数据库作为数据源来驱动API测试，实现更灵活、更强大的测试数据管理。