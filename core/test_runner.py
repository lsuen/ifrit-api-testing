#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试执行器
负责执行API自动化测试
"""

import os
import platform
import subprocess
import logging

from config.config import Config
from core.case_discovery import format_cli_plan, format_cli_result, parse_pytest_result


class TestRunner:
    """测试执行器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        test_path=None,
        test_type=None,
        env_names=None,
        suite=None,
        global_auth=False,
    ):
        """运行测试并输出 CI 友好摘要。"""
        try:
            resolved_suite = suite
            if not resolved_suite and test_path:
                from core.case_discovery import infer_suite_from_path

                resolved_suite = infer_suite_from_path(test_path)

            plan = format_cli_plan(
                data_format=test_type if test_type and test_type != "all" else None,
                suite=resolved_suite,
                test_path=test_path,
                env_names=env_names,
                global_auth=global_auth,
            )
            print(plan)

            config = Config(env_names=env_names)
            os.makedirs("./reports/allure_reports", exist_ok=True)

            cmd = [
                "pytest",
                "-v",
                "--alluredir=./reports/allure_reports",
                "--clean-alluredir",
            ]

            if env_names:
                for env_name in env_names:
                    cmd.extend(["--env", env_name])

            if test_path and test_path.endswith((".csv", ".xlsx", ".xls", ".json")):
                cmd.extend(["--test-data-file", test_path])

            if resolved_suite:
                cmd.extend(["--suite", resolved_suite])
            elif test_path:
                normalized = test_path.replace("\\", "/")
                if "fixtures/ai" in normalized:
                    cmd.extend(["--suite", "ai"])
                elif "fixtures/smoke" in normalized:
                    cmd.extend(["--suite", "smoke"])

            if global_auth:
                cmd.append("--global-auth")

            driver_path = self._resolve_driver(test_path, test_type)
            cmd.insert(1, driver_path)

            self.logger.info("执行命令: %s", " ".join(cmd))
            if platform.system().lower() == "windows":
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=__import__("sys").stderr)

            summary = parse_pytest_result(result.stdout, result.stderr, result.returncode)
            print(format_cli_result(summary))

            return result.returncode

        except Exception as error:
            self.logger.error("执行测试时发生异常: %s", error)
            import traceback

            self.logger.error("详细错误信息:\n%s", traceback.format_exc())
            print(f"[IFRIT] ── 执行结果 ── status=ERROR exit=1 msg={error}")
            return 1

    @staticmethod
    def _resolve_driver(test_path, test_type) -> str:
        """根据类型/文件选择唯一驱动，避免 drivers/ 重复执行。"""
        if test_path:
            if test_path.endswith(".csv"):
                return "drivers/test_api_csv_driver.py"
            if test_path.endswith((".xlsx", ".xls")):
                return "drivers/test_api_excel_driver.py"
            if test_path.endswith(".json"):
                return "drivers/test_api_json_driver.py"
            if test_path.endswith(".py"):
                return test_path

        mapping = {
            "excel": "drivers/test_api_excel_driver.py",
            "csv": "drivers/test_api_csv_driver.py",
            "json": "drivers/test_api_json_driver.py",
            "all": "drivers/test_all_drivers.py",
        }
        if test_type in mapping:
            return mapping[test_type]

        return "drivers/test_all_drivers.py"
