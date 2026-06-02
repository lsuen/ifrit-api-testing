#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：JSON 格式 API 测试驱动
创建时间：2025-09-28
"""
import pytest

from core.assert_handler import AssertHandler
from core.case_discovery import FORMAT_JSON, build_case_param_id, discover_and_load
from core.test_executor import TestExecutor


def _load_cases(pytest_config) -> list:
    single_file = pytest_config.getoption("--test-data-file") or None
    suite = pytest_config.getoption("--suite") or None
    env_names = pytest_config.getoption("--env") or None

    result = discover_and_load(
        data_format=FORMAT_JSON,
        suite=suite,
        single_file=single_file,
        env_names=env_names,
    )
    for case in result.cases:
        case["_suite"] = result.suite
    return result.cases


def pytest_generate_tests(metafunc):
    if "case" not in metafunc.fixturenames:
        return

    cases = _load_cases(metafunc.config)
    if not cases:
        pytest.skip("未找到任何 JSON 测试用例")

    case_ids = [build_case_param_id(case) for case in cases]
    metafunc.parametrize("case", cases, ids=case_ids)


class TestJsonDriver:
    """JSON 测试用例执行器。"""

    def test_api_case(self, case, request_handler, auth_manager, data_handler):
        assert_handler = AssertHandler()
        executor = TestExecutor(
            request_handler, data_handler, assert_handler, auth_manager=auth_manager
        )
        executor.execute_test_case(case)
