#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：CSV 格式 API 测试驱动
核心功能：加载 CSV 用例并执行，支持 --test-data-file / --suite
创建时间：2025-09-10
"""
import pytest

from core.assert_handler import AssertHandler
from core.case_discovery import FORMAT_CSV, build_case_param_id, discover_and_load
from core.test_executor import TestExecutor


def _load_cases(pytest_config) -> list:
    """通过公共发现模块加载 CSV 用例。"""
    single_file = pytest_config.getoption("--test-data-file") or None
    suite = pytest_config.getoption("--suite") or None
    env_names = pytest_config.getoption("--env") or None

    result = discover_and_load(
        data_format=FORMAT_CSV,
        suite=suite,
        single_file=single_file,
        env_names=env_names,
    )
    for case in result.cases:
        case["_suite"] = result.suite
    return result.cases


def pytest_generate_tests(metafunc):
    """动态参数化：支持 --test-data-file / --suite。"""
    if "case" not in metafunc.fixturenames:
        return

    cases = _load_cases(metafunc.config)
    if not cases:
        pytest.skip("未找到任何 CSV 测试用例（检查 --suite manual|ai|smoke）")

    case_ids = [build_case_param_id(case) for case in cases]
    metafunc.parametrize("case", cases, ids=case_ids)


class TestCsvDriver:
    """CSV 测试用例执行器。"""

    def test_api_case(self, case, request_handler, auth_manager, data_handler):
        """执行单条 CSV API 测试用例。"""
        assert_handler = AssertHandler()
        executor = TestExecutor(
            request_handler, data_handler, assert_handler, auth_manager=auth_manager
        )
        executor.execute_test_case(case)
