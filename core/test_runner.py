#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试执行器
负责执行API自动化测试
"""

import logging
import os
import subprocess

from config.config import Config
from core.case_discovery import format_cli_plan, format_cli_result, parse_pytest_result
from core.retention import maybe_auto_clean_before_run
from core.run_artifacts import create_run_directory
from utils.logger import configure_logging, set_console_level


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
        test_assist=False,
    ):
        """运行测试：控制台仅输出计划/逐条结果/汇总，详细 IO 写入 logs/。"""
        try:
            resolved_suite = suite
            if not resolved_suite and test_type == "all":
                resolved_suite = Config.SUITE_ALL
            elif not resolved_suite and test_path:
                from core.case_discovery import infer_suite_from_path

                resolved_suite = infer_suite_from_path(test_path)

            os.environ["IFRIT_CLI_MODE"] = "1"
            configure_logging(console_level=logging.WARNING)
            set_console_level(logging.WARNING)

            cfg = Config(env_names=env_names)
            maybe_auto_clean_before_run(cfg)
            run_paths = create_run_directory(
                config=cfg,
                suite=resolved_suite,
                test_type=test_type,
            )
            os.environ["IFRIT_RUN_ID"] = run_paths["run_id"]

            plan = format_cli_plan(
                data_format=test_type if test_type and test_type != "all" else None,
                suite=resolved_suite,
                test_path=test_path,
                env_names=env_names,
                global_auth=global_auth,
            )
            print(plan)
            print(f"[IFRIT] 报告目录=reports/runs/{run_paths['run_id']}")

            allure_dir = run_paths["allure_dir"]

            cmd = [
                "pytest",
                "-q",
                "--no-header",
                "--tb=line",
                f"--alluredir={allure_dir}",
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
            result = subprocess.run(cmd, capture_output=True, text=True)

            for line in f"{result.stdout}\n{result.stderr}".splitlines():
                idx = line.find("[IFRIT]")
                if idx >= 0:
                    print(line[idx:])

            summary = parse_pytest_result(result.stdout, result.stderr, result.returncode)
            print(format_cli_result(summary))

            if summary.get("failed", 0) > 0 or summary.get("error", 0) > 0:
                print("[IFRIT] 失败详情见 logs/errors/ 与 Allure 报告")
                if test_assist:
                    from core.test_assist import ASSIST_MARKER, analyze_test_output
                    import json as _json

                    try:
                        assist = analyze_test_output(
                            result.stdout,
                            result.stderr,
                            run_id=run_paths["run_id"],
                            suite=resolved_suite,
                        )
                        print(ASSIST_MARKER + _json.dumps(assist, ensure_ascii=False))
                        print(
                            f"[IFRIT] TEST_ASSIST done diagnosis={len(assist.get('diagnosis', []))} "
                            f"retain=user_decision"
                        )
                    except Exception as assist_error:
                        print(f"[IFRIT] TEST_ASSIST failed: {assist_error}")

            os.environ.pop("IFRIT_CLI_MODE", None)
            os.environ.pop("IFRIT_RUN_ID", None)
            configure_logging(console_level=logging.INFO)

            return result.returncode

        except Exception as error:
            self.logger.error("执行测试时发生异常: %s", error)
            import traceback

            self.logger.error("详细错误信息:\n%s", traceback.format_exc())
            print(f"[IFRIT] ── 执行结果 ── status=ERROR exit=1 msg={error}")
            os.environ.pop("IFRIT_CLI_MODE", None)
            os.environ.pop("IFRIT_RUN_ID", None)
            configure_logging(console_level=logging.INFO)
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
