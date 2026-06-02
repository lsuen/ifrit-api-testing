#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：CSV 格式 API 测试驱动
核心功能：加载 CSV 用例并执行，支持 --test-data-file 指定单文件
创建时间：2025-09-10
"""
import os

import allure
import pytest

from config.config import Config
from core.assert_handler import AssertHandler
from core.test_executor import TestExecutor
from utils.test_case_reader import DataHandler
from utils.logger import logger

config = Config()


def load_csv_test_cases(pytest_config) -> list:
    """根据 pytest 配置加载 CSV 测试用例。"""
    single_file = pytest_config.getoption("--test-data-file") or ""
    suite = pytest_config.getoption("--suite") or Config.SUITE_MANUAL

    if single_file:
        if os.path.isabs(single_file):
            test_files = [single_file]
        else:
            test_files = [os.path.join(config.base_dir, single_file)]
    else:
        test_files = config.get_csv_test_files(suite)

    all_cases = []
    logger.info("查找 CSV 测试文件，共 %s 个", len(test_files))
    for file_path in test_files:
        logger.info("读取测试文件: %s", file_path)
        cases = DataHandler().read_test_cases(file_path)
        if cases:
            all_cases.extend(cases)
            logger.info("从 %s 加载了 %s 条用例", file_path, len(cases))
        else:
            logger.warning("从 %s 未加载到用例", file_path)

    logger.info("总共加载 %s 条 CSV 用例", len(all_cases))
    return all_cases


def pytest_generate_tests(metafunc):
    """动态参数化：支持 --test-data-file 单文件执行。"""
    if "case" not in metafunc.fixturenames:
        return

    cases = load_csv_test_cases(metafunc.config)
    if not cases:
        pytest.skip("未找到任何 CSV 测试用例")

    case_ids = [f"{case['case_id']} - {case['case_name']}" for case in cases]
    metafunc.parametrize("case", cases, ids=case_ids)


@allure.feature("API接口测试")
class TestCsvDriver:
    """CSV 测试用例执行器。"""

    @allure.story("CSV测试用例执行")
    def test_api_case(self, case, request_handler, auth_manager, data_handler):
        """执行单条 CSV API 测试用例。"""
        logger.info("开始执行用例: %s", case["case_name"])
        assert_handler = AssertHandler()
        executor = TestExecutor(
            request_handler, data_handler, assert_handler, auth_manager=auth_manager
        )
        executor.execute_test_case(case)
