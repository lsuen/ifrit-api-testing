#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    : 
# @File    : test_all_drivers.py
# @Software: PyCharm
"""
统一测试用例执行器，支持Excel格式
"""

import pytest
import json
import allure
import os

from core.test_executor import TestExecutor
from utils.test_case_reader import DataHandler
from core.assert_handler import AssertHandler
from core.data_handler import DataHandler as GlobalDataHandler
from config.config import Config
from utils.logger import logger

# 全局数据处理器
data_handler = GlobalDataHandler()

# 获取Excel测试用例
# 注意：这里暂时无法获取到命令行参数，所以使用默认配置
# 实际环境中，RequestHandler会在conftest.py中正确初始化
config = Config()
all_test_cases = []
test_files = config.get_excel_test_files()
logger.info(f"查找所有测试文件，找到 {len(test_files)} 个文件")
for file_path in test_files:
    logger.info(f"读取测试文件: {file_path}")
    cases = DataHandler().read_test_cases(file_path)
    if cases:
        all_test_cases.extend(cases)
        logger.info(f"从 {file_path} 加载了 {len(cases)} 条测试用例")
    else:
        logger.warning(f"从 {file_path} 未加载到测试用例")

# 如果没有测试用例，跳过测试
if not all_test_cases:
    logger.warning("未找到任何测试用例，跳过测试")
    pytest.skip("未找到任何测试用例", allow_module_level=True)
else:
    logger.info(f"总共加载了 {len(all_test_cases)} 条测试用例")

# 为测试用例生成ID列表
test_case_ids = [f"{case['case_id']} - {case['case_name']}" for case in all_test_cases]


@allure.feature("API接口测试")
class TestAllDrivers:

    def setup_method(self):
        """
        测试方法级别的初始化
        """
        logger.debug("初始化测试方法")
        # 从conftest.py获取已正确配置的request_handler
        pass

    @allure.story("Excel测试用例执行")
    @pytest.mark.parametrize("case", all_test_cases, ids=test_case_ids)
    def test_api_case(self, case, request_handler):
        """
        利用执行器执行用例

        Args:
            case (dict): 测试用例数据
            request_handler: 请求处理器fixture
        """
        self.assert_handler = AssertHandler()
        # 创建测试执行器实例
        self.test_executor = TestExecutor(request_handler, data_handler, self.assert_handler)
        self.test_executor.execute_test_case(case)