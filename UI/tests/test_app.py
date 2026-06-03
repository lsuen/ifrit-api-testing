#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/06/02
# @Author  : 孙文龙
# @File    : test_app.py
# @Software: PyCharm
# @Desc    : ifrit-apitest Web UI 单元测试，验证核心功能是否正常

import os
import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加 UI 目录到路径
UI_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(UI_DIR))

from app import app, load_config, load_commands_map, list_files, validate_command_params


class TestConfigLoading(unittest.TestCase):
    """测试配置加载功能"""
    
    def test_load_config_success(self):
        """测试配置文件加载成功"""
        config = load_config()
        
        self.assertIn("ifrit", config)
        self.assertIn("server", config)
        self.assertIn("paths", config)
        self.assertIn("root_path_resolved", config["ifrit"])
        
    def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        with patch("app.UI_DIR", Path("/nonexistent")):
            with self.assertRaises(FileNotFoundError):
                load_config()
    
    def test_load_commands_map_success(self):
        """测试命令映射配置加载成功"""
        commands = load_commands_map()
        
        self.assertIn("test_run", commands)
        self.assertIn("ai_generate", commands)
        self.assertIn("cmd", commands["test_run"])
        self.assertIn("params", commands["test_run"])


class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def test_list_files_empty_directory(self):
        """测试空目录文件列表"""
        with patch("pathlib.Path.exists", return_value=False):
            files = list_files("/nonexistent")
            self.assertEqual(files, [])
    
    def test_list_files_with_extensions(self):
        """测试带扩展名过滤的文件列表"""
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.suffix = ".csv"
        mock_file.name = "test.csv"
        mock_file.stat().st_size = 1024
        mock_file.stat().st_mtime = 1622548800
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.iterdir", return_value=[mock_file]):
                files = list_files("/test", [".csv"])
                self.assertEqual(len(files), 1)
                self.assertEqual(files[0]["name"], "test.csv")
    
    def test_validate_command_params_success(self):
        """测试参数验证成功"""
        params = {"format": "csv", "env": "dev"}
        command_config = {
            "params": {
                "format": {"type": "select"},
                "env": {"type": "select"}
            }
        }
        
        is_valid, error_msg = validate_command_params(params, command_config)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_command_params_missing(self):
        """测试参数验证失败（缺少参数）"""
        params = {"format": "csv"}
        command_config = {
            "params": {
                "format": {"type": "select"},
                "env": {"type": "select"}
            }
        }
        
        is_valid, error_msg = validate_command_params(params, command_config)
        self.assertFalse(is_valid)
        self.assertIn("缺少必要参数", error_msg)


class TestFlaskRoutes(unittest.TestCase):
    """测试 Flask 路由"""
    
    def setUp(self):
        """测试前准备"""
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        # 初始化配置
        import app as app_module
        app_module.CONFIG = {
            "ifrit": {
                "root_path_resolved": UI_DIR.parent,
                "python_bin": "python",
                "cli_script": "main.py"
            },
            "server": {"host": "0.0.0.0", "port": 5001, "debug": False},
            "paths": {
                "data": "data",
                "reports": "reports",
                "logs": "logs",
                "api_docs": "api_docs"
            }
        }
        app_module.COMMANDS_MAP = {
            "test_run": {
                "cmd": "{python} {script} --type {format} --env {env}",
                "params": {
                    "format": {"type": "select"},
                    "env": {"type": "select"}
                }
            }
        }
    
    def test_index_page(self):
        """测试首页加载"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("仪表盘".encode("utf-8"), response.data)
    
    def test_execute_page_get(self):
        """测试执行控制台页面加载"""
        response = self.client.get("/execute")
        self.assertEqual(response.status_code, 200)
        self.assertIn("执行控制台".encode("utf-8"), response.data)
    
    def test_reports_page(self):
        """测试报告中心页面加载"""
        response = self.client.get("/reports")
        self.assertEqual(response.status_code, 200)
        self.assertIn("报告中心".encode("utf-8"), response.data)
    
    def test_cases_page(self):
        """测试用例管理页面加载"""
        response = self.client.get("/cases")
        self.assertEqual(response.status_code, 200)
        self.assertIn("用例管理".encode("utf-8"), response.data)
    
    def test_ai_page(self):
        """测试 AI 生成页面加载"""
        response = self.client.get("/ai")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI 生成".encode("utf-8"), response.data)
    
    def test_get_envs_api(self):
        """测试获取环境列表 API"""
        response = self.client.get("/api/envs")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("environments", data)
    
    def test_execute_post_missing_file(self):
        """测试执行测试（缺少文件参数）"""
        response = self.client.post("/execute", json={
            "command": "test_run",
            "params": {"format": "csv", "env": "dev"}
        })
        # 应该返回成功（进程已启动），但实际执行会失败
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("process_id", data)
    
    def test_get_files_api(self):
        """测试获取文件列表 API"""
        response = self.client.post("/api/files", json={
            "dir": "data",
            "extensions": [".csv"]
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("files", data)
    
    def test_read_case_file_not_found(self):
        """测试读取用例（文件不存在）"""
        response = self.client.post("/cases/read", json={
            "file_path": "/nonexistent/file.csv"
        })
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_execute_status_not_found(self):
        """测试查询执行状态（进程不存在）"""
        response = self.client.get("/execute/status/nonexistent")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_cancel_execute_not_found(self):
        """测试取消执行（进程不存在）"""
        response = self.client.post("/execute/cancel/nonexistent")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)


class TestSSEStream(unittest.TestCase):
    """测试 SSE 日志流"""
    
    def setUp(self):
        """测试前准备"""
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        import app as app_module
        app_module.CONFIG = {
            "ifrit": {"root_path_resolved": UI_DIR.parent},
            "paths": {"logs": "logs"}
        }
    
    @unittest.skip("SSE 流测试需要异步处理，暂跳过")
    def test_sse_stream_process_not_found(self):
        """测试 SSE 流（进程不存在）"""
        response = self.client.get("/execute/stream/nonexistent")
        # SSE 流会持续等待，但进程不存在会返回空数据
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
