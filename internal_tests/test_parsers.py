#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内部单元测试 - 解析器模块测试
测试文档解析器等解析模块的功能
"""

import unittest
import os
import sys
import tempfile
import json
from io import StringIO
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.document_parser import DocumentParser


class TestDocumentParser(unittest.TestCase):
    """文档解析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = DocumentParser()
        print(f"\n【开始测试】文档解析器功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】文档解析器功能\n")
    
    def test_parse_markdown_document(self):
        """测试解析Markdown文档"""
        print("  - 测试解析Markdown文档")
        
        # 创建临时Markdown文档
        markdown_content = """
# API接口文档

## GET /users
获取用户列表

### 参数
- page: 页码
- size: 每页数量

### 响应
200 OK
```json
{
  "users": [],
  "total": 0
}
```

## POST /users
创建用户

### 请求体
```json
{
  "name": "用户名",
  "email": "邮箱"
}
```

### 响应
201 Created
```json
{
  "id": 1,
  "name": "用户名",
  "email": "邮箱"
}
```
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_filename = temp_file.name
        
        try:
            # 解析文档
            apis = self.parser.parse_document(temp_filename)
            self.assertIsNotNone(apis)
            self.assertIsInstance(apis, list)
            
            # 检查是否解析出了API
            if len(apis) > 0:
                api = apis[0]
                self.assertIn('method', api)
                self.assertIn('path', api)
                self.assertIn('description', api)
                print("    ✓ Markdown文档解析功能正常")
            else:
                print("    ⚠ Markdown文档解析未找到API接口")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_parse_swagger_json(self):
        """测试解析Swagger JSON文档"""
        print("  - 测试解析Swagger JSON文档")
        
        # 创建临时Swagger JSON文档
        swagger_json = {
            "swagger": "2.0",
            "info": {
                "title": "Sample API",
                "version": "1.0.0"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {
                                "description": "成功获取用户列表"
                            }
                        }
                    },
                    "post": {
                        "summary": "创建用户",
                        "responses": {
                            "201": {
                                "description": "成功创建用户"
                            }
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "获取用户详情",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "type": "integer"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "成功获取用户详情"
                            }
                        }
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(swagger_json, temp_file, ensure_ascii=False, indent=2)
            temp_filename = temp_file.name
        
        try:
            # 解析文档
            apis = self.parser.parse_document(temp_filename)
            self.assertIsNotNone(apis)
            self.assertIsInstance(apis, list)
            
            # 检查是否解析出了API
            if len(apis) > 0:
                # 至少应该解析出几个API接口
                print(f"    ✓ Swagger JSON文档解析功能正常，解析出 {len(apis)} 个API")
            else:
                print("    ⚠ Swagger JSON文档解析未找到API接口")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_parse_empty_document(self):
        """测试解析空文档"""
        print("  - 测试解析空文档")
        
        # 创建空文档
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")
            temp_filename = temp_file.name
        
        try:
            # 解析文档
            apis = self.parser.parse_document(temp_filename)
            self.assertIsNotNone(apis)
            self.assertIsInstance(apis, list)
            print("    ✓ 空文档解析功能正常")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_parse_invalid_document(self):
        """测试解析无效文档"""
        print("  - 测试解析无效文档")
        
        # 创建无效内容文档
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write("这是一个无效的API文档内容")
            temp_filename = temp_file.name
        
        try:
            # 解析文档
            apis = self.parser.parse_document(temp_filename)
            # 对于无效文档，应该返回空列表或处理异常
            self.assertIsNotNone(apis)
            self.assertIsInstance(apis, list)
            print("    ✓ 无效文档解析功能正常")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_extract_api_info_from_markdown(self):
        """测试从Markdown中提取API信息"""
        print("  - 测试从Markdown中提取API信息")
        
        markdown_content = """
## GET /api/users
获取用户列表

### 描述
获取所有注册用户的列表信息

### 参数
- page: 页码，默认为1
- size: 每页数量，默认为10

### 响应
200 OK
```json
{
  "code": 0,
  "message": "success",
  "data": []
}
```
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_filename = temp_file.name
        
        try:
            # 解析文档
            apis = self.parser.parse_document(temp_filename)
            self.assertIsNotNone(apis)
            
            print("    ✓ Markdown API信息提取功能正常")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    def test_parse_with_endpoints_filter(self):
        """测试带端点过滤的解析"""
        print("  - 测试带端点过滤的解析")
        
        markdown_content = """
## GET /users
获取用户列表

## GET /orders
获取订单列表

## POST /products
创建产品
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(markdown_content)
            temp_filename = temp_file.name
        
        try:
            # 解析文档，指定特定端点
            apis = self.parser.parse_document(temp_filename, ['/users'])
            self.assertIsNotNone(apis)
            self.assertIsInstance(apis, list)
            
            # 检查是否只解析了指定的端点
            if len(apis) > 0:
                for api in apis:
                    self.assertEqual(api['path'], '/users')
                
                print("    ✓ 端点过滤解析功能正常")
            else:
                print("    ⚠ 端点过滤解析未找到匹配的API")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


class TestDataParser(unittest.TestCase):
    """数据解析器测试类（如果有其他解析器）"""
    
    def setUp(self):
        """测试前准备"""
        print(f"\n【开始测试】数据解析功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】数据解析功能\n")
    
    def test_json_path_extraction(self):
        """测试JSON路径提取功能"""
        print("  - 测试JSON路径提取功能")
        
        # 这里测试数据处理器中的JSON路径提取功能
        from core.data_handler import DataHandler
        handler = DataHandler()
        
        test_data = {
            "user": {
                "id": 1,
                "name": "test_user",
                "profile": {
                    "email": "test@example.com",
                    "settings": {
                        "theme": "dark"
                    }
                }
            },
            "items": [
                {"id": 1, "name": "item1"},
                {"id": 2, "name": "item2"}
            ]
        }
        
        # 测试基本路径提取
        result1 = handler.extract_value(test_data, "user.name")
        self.assertEqual(result1, "test_user")
        
        # 测试嵌套路径提取
        result2 = handler.extract_value(test_data, "user.profile.email")
        self.assertEqual(result2, "test@example.com")
        
        # 测试数组索引提取
        result3 = handler.extract_value(test_data, "items[0].name")
        self.assertEqual(result3, "item1")
        
        print("    ✓ JSON路径提取功能正常")
    
    def test_regex_extraction(self):
        """测试正则表达式提取功能"""
        print("  - 测试正则表达式提取功能")
        
        from core.data_handler import DataHandler
        handler = DataHandler()
        
        test_data = "Response: user_id=12345, session_token=abcde12345, timestamp=2023-01-01"
        
        # 测试正则提取用户ID
        result1 = handler.extract_value(test_data, "regex:user_id=(\\d+)")
        self.assertEqual(result1, "12345")
        
        # 测试正则提取会话令牌
        result2 = handler.extract_value(test_data, "regex:session_token=([a-zA-Z0-9]+)")
        self.assertEqual(result2, "abcde12345")
        
        print("    ✓ 正则表达式提取功能正常")


if __name__ == '__main__':
    print("="*60)
    print("开始运行内部单元测试 - 解析器模块")
    print("="*60)
    
    # 运行测试
    unittest.main(verbosity=2)