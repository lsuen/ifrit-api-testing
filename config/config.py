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

    SUITE_MANUAL = "manual"
    SUITE_AI = "ai"
    SUITE_SMOKE = "smoke"
    SUITE_ALL = "all"
    ALL_SUITES = (SUITE_MANUAL, SUITE_AI, SUITE_SMOKE)

    def __init__(self, env_names: Optional[List[str]] = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.settings_dir = os.path.join(self.config_dir, "settings")
        self.fixtures_dir = os.path.join(self.base_dir, "fixtures")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.testcases_dir = os.path.join(self.base_dir, "drivers")
        self.utils_dir = os.path.join(self.base_dir, "utils")
        self.core_dir = os.path.join(self.base_dir, "core")

        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.fixtures_dir, exist_ok=True)

        self.app_config = load_ini("app.ini")
        self.env_config = load_ini("env_config.ini")
        self.test_data_config = load_ini("test_data.ini")
        self.column_mapping_config = load_ini("column_mapping.ini")
        self.auth_config = load_ini("auth.ini")
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

    def get_retention_config(self) -> Dict[str, Any]:
        """获取日志/报告保留策略。"""
        section = "retention"
        if not self.app_config.has_section(section):
            return {
                "logs_keep_days": 14,
                "reports_keep_days": 7,
                "reports_keep_last": 20,
                "auto_clean_before_run": False,
            }
        return {
            "logs_keep_days": self.app_config.getint(section, "logs_keep_days", fallback=14),
            "reports_keep_days": self.app_config.getint(section, "reports_keep_days", fallback=7),
            "reports_keep_last": self.app_config.getint(section, "reports_keep_last", fallback=20),
            "auto_clean_before_run": self.app_config.getboolean(
                section, "auto_clean_before_run", fallback=False
            ),
        }

    def is_main_log_enabled(self) -> bool:
        """是否写入 logs/api_automation.log（默认关闭，避免与 daily 重复增长）。"""
        return self.app_config.getboolean("logging", "main_log_enabled", fallback=False)

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

    def _resolve_path(self, relative_path: str) -> str:
        """将 ini 中的相对路径转为绝对路径。"""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.base_dir, relative_path)

    def get_fixtures_root(self) -> str:
        """获取 fixtures 根目录。"""
        root = self.test_data_config.get("paths", "root", fallback="fixtures")
        return self._resolve_path(root)

    def get_suite_csv_dir(self, suite: str = SUITE_MANUAL) -> str:
        """按套件（manual/ai/smoke/all）获取 CSV 目录。"""
        if suite == self.SUITE_ALL:
            return self.get_manual_csv_dir()
        section = suite if suite in self.ALL_SUITES else self.SUITE_MANUAL
        csv_dir = self.test_data_config.get(section, "csv_dir", fallback=f"fixtures/{section}/csv")
        return self._resolve_path(csv_dir)

    def get_manual_csv_dir(self) -> str:
        return self.get_suite_csv_dir(self.SUITE_MANUAL)

    def get_ai_csv_dir(self) -> str:
        return self.get_suite_csv_dir(self.SUITE_AI)

    def get_smoke_csv_dir(self) -> str:
        return self.get_suite_csv_dir(self.SUITE_SMOKE)

    def get_ai_output_dir(self) -> str:
        """AI 生成用例默认输出目录。"""
        output_dir = self.test_data_config.get(
            "ai", "default_output_dir", fallback="fixtures/ai/csv"
        )
        return self._resolve_path(output_dir)

    def get_test_files(self) -> Any:
        """获取测试文件列表配置。"""
        files = self.test_data_config.get("test_files", "files", fallback="all")
        if files.lower() == "all":
            return "all"
        file_list = [item.strip() for item in files.split(",")]
        manual_dir = self.get_manual_csv_dir()
        return [
            os.path.join(manual_dir, file_name) if not os.path.isabs(file_name) else file_name
            for file_name in file_list
        ]

    def get_data_dir(self) -> str:
        """兼容旧接口：返回 fixtures 根目录。"""
        return self.get_fixtures_root()

    def get_excel_dir(self, suite: str = SUITE_MANUAL) -> str:
        """获取 Excel 测试数据目录。"""
        excel_dir = self.test_data_config.get(
            suite, "excel_dir", fallback=f"fixtures/{suite}/excel"
        )
        return self._resolve_path(excel_dir)

    def get_csv_dir(self, suite: str = SUITE_MANUAL) -> str:
        """获取 CSV 测试数据目录（默认 manual）。"""
        return self.get_suite_csv_dir(suite)

    def get_json_dir(self, suite: str = SUITE_MANUAL) -> str:
        """获取 JSON 测试数据目录。"""
        json_dir = self.test_data_config.get(
            suite, "json_dir", fallback=f"fixtures/{suite}/json"
        )
        return self._resolve_path(json_dir)

    def _collect_files_from_dir(self, directory: str, extensions: tuple) -> List[str]:
        """扫描目录下指定后缀的文件。"""
        if not os.path.exists(directory):
            return []
        return sorted(
            os.path.join(directory, file_name)
            for file_name in os.listdir(directory)
            if file_name.endswith(extensions)
        )

    def get_all_test_files(self, suite: str = SUITE_MANUAL) -> List[str]:
        """获取 CSV + Excel + JSON 测试文件路径。"""
        return (
            self.get_csv_test_files(suite)
            + self.get_excel_test_files(suite)
            + self.get_json_test_files(suite)
        )

    def get_csv_test_files(self, suite: str = SUITE_MANUAL) -> List[str]:
        """获取 CSV 测试文件路径。"""
        if suite == self.SUITE_ALL:
            files: List[str] = []
            for item in self.ALL_SUITES:
                files.extend(self._collect_files_from_dir(self.get_suite_csv_dir(item), (".csv",)))
            return sorted(set(files))
        return self._collect_files_from_dir(self.get_csv_dir(suite), (".csv",))

    def get_excel_test_files(self, suite: str = SUITE_MANUAL) -> List[str]:
        """获取 Excel 测试文件路径。"""
        if suite == self.SUITE_ALL:
            files: List[str] = []
            for item in self.ALL_SUITES:
                files.extend(self._collect_files_from_dir(self.get_excel_dir(item), (".xlsx", ".xls")))
            return sorted(set(files))
        return self._collect_files_from_dir(self.get_excel_dir(suite), (".xlsx", ".xls"))

    def get_json_test_files(self, suite: str = SUITE_MANUAL) -> List[str]:
        """获取 JSON 测试文件路径。"""
        if suite == self.SUITE_ALL:
            files: List[str] = []
            for item in self.ALL_SUITES:
                files.extend(self._collect_files_from_dir(self.get_json_dir(item), (".json",)))
            return sorted(set(files))
        return self._collect_files_from_dir(self.get_json_dir(suite), (".json",))


if __name__ == "__main__":
    cfg = Config()
    print("manual csv:", cfg.get_csv_test_files())
    print("smoke csv:", cfg.get_csv_test_files(Config.SUITE_SMOKE))
