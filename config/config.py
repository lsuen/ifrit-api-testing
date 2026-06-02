#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
文件用途：框架全局配置管理
核心功能：环境 URL、测试数据路径、日志、数据库等运行时配置
创建时间：2025-09-09
"""
import os
from typing import Any, Dict, List, Optional

from config.loader import get_env_value, load_ini


class Config:
    """全局配置类"""

    def __init__(self, env_names: Optional[List[str]] = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.settings_dir = os.path.join(self.config_dir, "settings")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.testcases_dir = os.path.join(self.base_dir, "drivers")
        self.utils_dir = os.path.join(self.base_dir, "utils")
        self.core_dir = os.path.join(self.base_dir, "core")

        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        self.app_config = load_ini("app.ini")
        self.env_config = load_ini("env_config.ini")
        self.test_data_config = load_ini("test_data.ini")
        self.column_mapping_config = load_ini("column_mapping.ini")
        self.current_envs = env_names or ["environment"]

    def get_base_url(self) -> str:
        """获取 API 基础 URL（.env IFRIT_BASE_URL 优先，否则按环境 profile）。"""
        override_url = get_env_value("IFRIT_BASE_URL")
        if override_url:
            return override_url

        for env in self.current_envs:
            if self.env_config.has_section(env) and self.env_config.has_option(env, "base_url"):
                return self.env_config.get(env, "base_url")

        return self.env_config.get("environment", "base_url", fallback="")

    def get_timeout(self) -> int:
        """获取请求超时时间（秒）。"""
        for env in self.current_envs:
            if self.env_config.has_section(env) and self.env_config.has_option(env, "timeout"):
                return self.env_config.getint(env, "timeout")
        return self.env_config.getint("environment", "timeout", fallback=30)

    def get_log_level(self) -> str:
        """获取日志级别。"""
        return self.app_config.get("logging", "level", fallback="INFO")

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库连接配置（账号密码来自 .env）。"""
        if not self.env_config.has_section("database"):
            return {}

        return {
            "host": self.env_config.get("database", "host", fallback="localhost"),
            "port": self.env_config.getint("database", "port", fallback=5432),
            "user": get_env_value("DB_USER"),
            "password": get_env_value("DB_PASSWORD"),
        }

    def get_test_files(self) -> Any:
        """获取测试文件列表配置。"""
        files = self.test_data_config.get("test_files", "files", fallback="all")
        if files.lower() == "all":
            return "all"
        file_list = [item.strip() for item in files.split(",")]
        data_dir = self.get_data_dir()
        return [
            os.path.join(data_dir, file_name) if not os.path.isabs(file_name) else file_name
            for file_name in file_list
        ]

    def get_data_dir(self) -> str:
        """获取测试数据根目录。"""
        data_dir = self.test_data_config.get("test_files", "data_dir", fallback="data")
        return os.path.join(self.base_dir, data_dir)

    def get_excel_dir(self) -> str:
        """获取 Excel 测试数据目录。"""
        excel_dir = self.test_data_config.get(
            "excel_files", "excel_dir", fallback="data/excel_data"
        )
        return os.path.join(self.base_dir, excel_dir)

    def get_csv_dir(self) -> str:
        """获取 CSV 测试数据目录。"""
        csv_dir = self.test_data_config.get(
            "csv_files", "csv_dir", fallback="data/csv_data"
        )
        return os.path.join(self.base_dir, csv_dir)

    def get_json_dir(self) -> str:
        """获取 JSON 测试数据目录。"""
        json_dir = self.test_data_config.get(
            "json_files", "json_dir", fallback="data/json_data"
        )
        return os.path.join(self.base_dir, json_dir)

    def _collect_files_from_dir(self, directory: str, extensions: tuple) -> List[str]:
        """扫描目录下指定后缀的文件。"""
        if not os.path.exists(directory):
            return []
        return [
            os.path.join(directory, file_name)
            for file_name in os.listdir(directory)
            if file_name.endswith(extensions)
        ]

    def get_all_test_files(self) -> List[str]:
        """获取 Excel + CSV 测试文件路径。"""
        return self.get_excel_test_files() + self.get_csv_test_files()

    def get_excel_test_files(self) -> List[str]:
        """获取 Excel 测试文件路径。"""
        return self._collect_files_from_dir(self.get_excel_dir(), (".xlsx", ".xls"))

    def get_csv_test_files(self) -> List[str]:
        """获取 CSV 测试文件路径。"""
        return self._collect_files_from_dir(self.get_csv_dir(), (".csv",))

    def get_json_test_files(self) -> List[str]:
        """获取 JSON 测试文件路径。"""
        return self._collect_files_from_dir(self.get_json_dir(), (".json",))


if __name__ == "__main__":
    print(Config().get_json_test_files())
