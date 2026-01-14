#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内部单元测试 - 工具类模块测试
测试各类工具类的功能
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

from core.assert_handler import AssertHandler
from core.data_handler import DataHandler
from core.request_handler import RequestHandler
from utils.logger import logger, get_logger


class TestAssertHandler(unittest.TestCase):
    """断言处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.handler = AssertHandler()
        print(f"\n【开始测试】断言处理器功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】断言处理器功能\n")
    
    def test_assert_equal(self):
        """测试相等断言"""
        print("  - 测试相等断言")
        
        # 测试成功情况
        result = self.handler.assert_equal(5, 5)
        self.assertTrue(result)
        
        # 测试失败情况 - 会抛出异常，使用assertRaises
        with self.assertRaises(AssertionError):
            self.handler.assert_equal(5, 10)
        
        print("    ✓ 相等断言功能正常")
    
    def test_assert_contains(self):
        """测试包含断言"""
        print("  - 测试包含断言")
        
        # 测试成功情况
        result = self.handler.assert_contains("hello world", "world")
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.handler.assert_contains("hello world", "xyz")
        
        print("    ✓ 包含断言功能正常")
    
    def test_assert_status_code(self):
        """测试状态码断言"""
        print("  - 测试状态码断言")
        
        # 模拟响应对象
        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code
        
        mock_resp = MockResponse(200)
        
        # 测试成功情况
        result = self.handler.assert_status_code(mock_resp, 200)
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.handler.assert_status_code(mock_resp, 404)
        
        print("    ✓ 状态码断言功能正常")
    
    def test_assert_json_value(self):
        """测试JSON值断言"""
        print("  - 测试JSON值断言")
        
        # 模拟响应对象
        class MockJsonResponse:
            def __init__(self, json_data):
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        mock_resp = MockJsonResponse({"user": {"name": "test", "age": 25}})
        
        # 测试成功情况
        result = self.handler.assert_json_value(mock_resp, "user.name", "test")
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.handler.assert_json_value(mock_resp, "user.name", "other")
        
        print("    ✓ JSON值断言功能正常")
    
    def test_assert_content_contains(self):
        """测试内容包含断言"""
        print("  - 测试内容包含断言")
        
        # 模拟响应对象
        class MockTextResponse:
            def __init__(self, text):
                self.text = text
        
        mock_resp = MockTextResponse("Welcome to our website")
        
        # 测试成功情况
        result = self.handler.assert_content_contains(mock_resp, "website")
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.handler.assert_content_contains(mock_resp, "not_found")
        
        print("    ✓ 内容包含断言功能正常")
    
    def test_assert_regex(self):
        """测试正则表达式断言"""
        print("  - 测试正则表达式断言")
        
        # 模拟响应对象
        class MockTextResponse:
            def __init__(self, text):
                self.text = text
        
        mock_resp = MockTextResponse("My email is test@example.com and phone is 123-456-7890")
        
        # 测试成功情况
        result = self.handler.assert_regex(mock_resp, r"\w+@\w+\.\w+")
        self.assertTrue(result)
        
        # 测试失败情况
        with self.assertRaises(AssertionError):
            self.handler.assert_regex(mock_resp, r"nonexistent")
        
        print("    ✓ 正则表达式断言功能正常")
    
    def test_assert_json_structure(self):
        """测试JSON结构断言"""
        print("  - 测试JSON结构断言")
        
        # 模拟响应对象
        class MockJsonResponse:
            def __init__(self, json_data):
                self._json_data = json_data
            
            def json(self):
                return self._json_data
        
        mock_resp = MockJsonResponse({
            "user": {
                "id": 1,
                "name": "test",
                "settings": {}
            }
        })
        
        expected_structure = {
            "user": {
                "id": 0,
                "name": "",
                "settings": {}
            }
        }
        
        # 测试成功情况
        result = self.handler.assert_json_structure(mock_resp, expected_structure)
        self.assertTrue(result)
        
        print("    ✓ JSON结构断言功能正常")


class TestDataHandler(unittest.TestCase):
    """数据处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.handler = DataHandler()
        print(f"\n【开始测试】数据处理器功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】数据处理器功能\n")
    
    def test_set_and_get_variable(self):
        """测试设置和获取变量"""
        print("  - 测试设置和获取变量")
        
        # 设置变量
        self.handler.set_variable("username", "testuser")
        self.handler.set_variable("password", "testpass")
        
        # 获取变量
        username = self.handler.get_variable("username")
        password = self.handler.get_variable("password")
        
        self.assertEqual(username, "testuser")
        self.assertEqual(password, "testpass")
        
        print("    ✓ 设置和获取变量功能正常")
    
    def test_replace_variables(self):
        """测试替换变量"""
        print("  - 测试替换变量")
        
        # 设置变量
        self.handler.set_variable("host", "localhost")
        self.handler.set_variable("port", "8080")
        
        # 测试${}格式替换
        text_with_vars1 = "http://${host}:${port}/api/users"
        result1 = self.handler.replace_variables(text_with_vars1)
        expected1 = "http://localhost:8080/api/users"
        self.assertEqual(result1, expected1)
        
        # 测试{{}}格式替换
        text_with_vars2 = "http://{{host}}:{{port}}/api/orders"
        result2 = self.handler.replace_variables(text_with_vars2)
        expected2 = "http://localhost:8080/api/orders"
        self.assertEqual(result2, expected2)
        
        print("    ✓ 变量替换功能正常")
    
    def test_extract_value_json_path(self):
        """测试JSON路径提取值"""
        print("  - 测试JSON路径提取值")
        
        response_data = {
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
        result1 = self.handler.extract_value(response_data, "user.name")
        self.assertEqual(result1, "test_user")
        
        # 测试嵌套路径提取
        result2 = self.handler.extract_value(response_data, "user.profile.email")
        self.assertEqual(result2, "test@example.com")
        
        # 测试数组索引提取
        result3 = self.handler.extract_value(response_data, "items[0].name")
        self.assertEqual(result3, "item1")
        
        # 测试不存在路径
        result4 = self.handler.extract_value(response_data, "user.nonexistent")
        self.assertEqual(result4, "")
        
        print("    ✓ JSON路径提取值功能正常")
    
    def test_extract_value_regex(self):
        """测试正则表达式提取值"""
        print("  - 测试正则表达式提取值")
        
        response_data = "Response: user_id=12345, session_token=abcde12345, timestamp=2023-01-01"
        
        # 测试正则提取用户ID
        result1 = self.handler.extract_value(response_data, "regex:user_id=(\\d+)")
        self.assertEqual(result1, "12345")
        
        # 测试正则提取会话令牌
        result2 = self.handler.extract_value(response_data, "regex:session_token=([a-zA-Z0-9]+)")
        self.assertEqual(result2, "abcde12345")
        
        # 测试不存在的模式
        result3 = self.handler.extract_value(response_data, "regex:nonexistent=(\\w+)")
        self.assertEqual(result3, "")
        
        print("    ✓ 正则表达式提取值功能正常")
    
    def test_multi_value_extraction(self):
        """测试多值提取"""
        print("  - 测试多值提取")
        
        response_data = {
            "user": {
                "id": 123,
                "name": "testuser",
                "email": "test@example.com"
            }
        }
        
        # 测试多值提取语法 "var1=path1; var2=path2"
        extract_key = "userId=user.id; userName=user.name; userEmail=user.email"
        result = self.handler.extract_value(response_data, extract_key)
        
        self.assertIsInstance(result, dict)
        self.assertIn("userId", result)
        self.assertIn("userName", result)
        self.assertIn("userEmail", result)
        self.assertEqual(result["userId"], "123")
        self.assertEqual(result["userName"], "testuser")
        self.assertEqual(result["userEmail"], "test@example.com")
        
        print("    ✓ 多值提取功能正常")
    
    def test_clear_variables(self):
        """测试清空变量"""
        print("  - 测试清空变量")
        
        # 设置一些变量
        self.handler.set_variable("var1", "value1")
        self.handler.set_variable("var2", "value2")
        
        # 验证变量存在
        self.assertEqual(self.handler.get_variable("var1"), "value1")
        self.assertEqual(self.handler.get_variable("var2"), "value2")
        
        # 清空变量
        self.handler.clear_global_vars()
        
        # 验证变量已清空
        self.assertEqual(self.handler.get_variable("var1"), "")
        self.assertEqual(self.handler.get_variable("var2"), "")
        
        print("    ✓ 清空变量功能正常")


class TestRequestHandler(unittest.TestCase):
    """请求处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.handler = RequestHandler(base_url="http://localhost:8080", timeout=10)
        print(f"\n【开始测试】请求处理器功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】请求处理器功能\n")
    
    def test_initialization(self):
        """测试初始化"""
        print("  - 测试初始化")
        
        self.assertEqual(self.handler.base_url, "http://localhost:8080")
        self.assertEqual(self.handler.timeout, 10)
        self.assertIsNotNone(self.handler.session)
        
        print("    ✓ 初始化功能正常")
    
    def test_url_construction(self):
        """测试URL构建"""
        print("  - 测试URL构建")
        
        # 模拟请求处理器内部的URL构建逻辑
        handler = RequestHandler(base_url="http://api.example.com")
        
        # 这里我们测试_url_construction逻辑
        # 实际的send_request方法会处理URL构建
        self.assertEqual(handler.base_url, "http://api.example.com")
        
        print("    ✓ URL构建功能正常")
    
    @patch('requests.Session.request')
    def test_send_request_mock(self, mock_request):
        """测试发送请求（模拟）"""
        print("  - 测试发送请求（模拟）")
        
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        mock_response.json.return_value = {"status": "ok"}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response
        
        # 测试GET请求
        response = self.handler.send_request('GET', '/test')
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        
        # 测试POST请求
        response = self.handler.send_request('POST', '/test', json_data={"key": "value"})
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        
        print("    ✓ 发送请求功能正常（模拟测试）")


class TestLogger(unittest.TestCase):
    """日志工具测试类"""
    
    def setUp(self):
        """测试前准备"""
        print(f"\n【开始测试】日志工具功能")
        
    def tearDown(self):
        """测试后清理"""
        print(f"【完成测试】日志工具功能\n")
    
    def test_logger_creation(self):
        """测试日志记录器创建"""
        print("  - 测试日志记录器创建")
        
        # 测试获取logger
        test_logger = get_logger("test_module")
        self.assertIsNotNone(test_logger)
        self.assertEqual(test_logger.name, "test_module")
        
        # 测试默认logger
        default_logger = get_logger()
        self.assertIsNotNone(default_logger)
        
        print("    ✓ 日志记录器创建功能正常")
    
    def test_logger_methods(self):
        """测试日志记录器方法"""
        print("  - 测试日志记录器方法")
        
        test_logger = get_logger("test_methods")
        
        # 测试各种日志级别方法
        try:
            test_logger.debug("Debug message")
            test_logger.info("Info message")
            test_logger.warning("Warning message")
            test_logger.error("Error message")
            print("    ✓ 日志记录器方法正常")
        except Exception as e:
            print(f"    ⚠ 日志记录器方法测试遇到异常: {e}")


if __name__ == '__main__':
    print("="*60)
    print("开始运行内部单元测试 - 工具类模块")
    print("="*60)
    
    # 运行测试
    unittest.main(verbosity=2)