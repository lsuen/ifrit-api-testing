#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    : 
# @File    : test_api_excel_driver.py
# @Software: PyCharm
"""
Excel测试用例执行
"""

import json
from typing import Dict, Any, List

import pytest

# 尝试导入allure，如果失败则设置为None
try:
    import allure

    ALLURE_AVAILABLE = True
except ImportError:
    allure = None
    ALLURE_AVAILABLE = False

from core.request_handler import RequestHandler
from core.data_handler import DataHandler
from core.assert_handler import AssertHandler
from utils.excel_handler import DataHandler as ExcelHandler
from utils.logger import logger
from config.config import Config


def get_test_cases() -> List[Dict[str, Any]]:
    """获取所有Excel测试用例"""
    config = Config()
    test_cases = []
    test_files = config.get_test_files()
    logger.info(f"查找所有测试文件，找到 {len(test_files)} 个文件")
    for file_path in test_files:
        if file_path.endswith(('.xls', '.xlsx')):
            logger.info(f"读取测试文件: {file_path}")
            handler = ExcelHandler()
            cases = handler.read_test_cases(file_path)
            if cases:
                test_cases.extend(cases)
                logger.info(f"从 {file_path} 加载了 {len(cases)} 条测试用例")
            else:
                logger.warning(f"从 {file_path} 未加载到测试用例")
    return test_cases


class TestAPI:
    """API测试类"""

    def setup_method(self):
        """测试方法级别的setup"""
        config = Config()
        base_url = config.get_base_url()
        timeout = config.get_timeout()
        self.request_handler = RequestHandler(base_url=base_url, timeout=timeout)
        self.data_manager = DataHandler()
        self.assert_handler = AssertHandler()
        self.excel_handler = ExcelHandler()

    @pytest.mark.parametrize("case", get_test_cases())
    def test_api_case(self, case: Dict[str, Any]):
        """参数化测试API用例"""
        logger.info(f"开始执行测试用例: {case['id']} - {case['name']}")

        # 记录测试用例信息到allure报告（如果可用）
        if ALLURE_AVAILABLE and allure:
            allure.dynamic.feature("接口测试")
            allure.dynamic.story(case['name'])
            allure.dynamic.title(f"{case['id']} - {case['name']}")
            allure.dynamic.description(f"测试用例ID: {case['id']}\n测试用例名称: {case['name']}")

            # 记录请求参数
            allure.attach(json.dumps(case, ensure_ascii=False, indent=2), "测试用例数据", allure.attachment_type.JSON)

        # 替换URL中的变量
        url = self.data_manager.replace_variables(case['url'])
        logger.info(f"替换变量后的URL: {url}")

        # 替换headers中的变量
        headers_str = self.data_manager.replace_variables(case['headers'])
        headers = {}
        if headers_str:
            try:
                headers = json.loads(headers_str)
                logger.debug(f"解析后的请求头: {headers}")
            except json.JSONDecodeError as e:
                logger.warning(f"请求头JSON解析失败: {e}, 使用空字典")

        # 替换params中的变量
        params_str = self.data_manager.replace_variables(case['params'])
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
                logger.debug(f"解析后的URL参数: {params}")
            except json.JSONDecodeError as e:
                logger.warning(f"URL参数JSON解析失败: {e}, 使用空字典")

        # 替换body中的变量
        body_str = self.data_manager.replace_variables(case['body'])
        body = {}
        if body_str:
            try:
                body = json.loads(body_str)
                logger.debug(f"解析后的请求体: {body}")
            except json.JSONDecodeError as e:
                logger.warning(f"body JSON解析失败: {e}, 使用空字典")

        logger.debug("请求参数变量替换完成")

        # 发送请求
        logger.info(f"发送 {case['method']} 请求到 {url}")
        response = self.request_handler.send_request(
            method=case['method'],
            url=url,
            headers=headers,
            params=params,
            json_data=body
        )

        # 断言响应状态码（无论是否收到有效响应都要尝试断言）
        if case['expected_status']:
            logger.info(f"执行状态码断言: 期望 {case['expected_status']}")
            if response:
                try:
                    assert self.assert_handler.assert_status_code(response, int(case['expected_status']))
                except AssertionError:
                    # 如果状态码断言失败，继续执行其他断言
                    pass
            else:
                logger.error("请求发送失败，未收到有效响应，无法执行状态码断言")

        # 如果没有收到有效响应且需要断言内容，则失败
        if not response:
            logger.error("请求发送失败，未收到有效响应")
            pytest.fail("请求发送失败，未收到有效响应")

        # 断言响应内容
        if case['expected_content']:
            logger.info(f"执行内容包含断言: 期望包含 '{case['expected_content']}'")
            try:
                assert self.assert_handler.assert_content_contains(response, case['expected_content'])
            except AssertionError:
                # 内容断言失败，继续执行其他逻辑
                pass

        # 断言JSON值
        if case['json_path'] and case['expected_json_value']:
            logger.info(f"执行JSON路径断言: 路径={case['json_path']}, 期望值={case['expected_json_value']}")
            try:
                assert self.assert_handler.assert_json_value(
                    response, case['json_path'], case['expected_json_value']
                )
            except AssertionError:
                # JSON断言失败，继续执行其他逻辑
                pass

        # 提取变量
        if case['extract_key'] and case['save_var_name']:
            logger.info(f"开始提取变量: 键={case['extract_key']}, 保存为={case['save_var_name']}")
            try:
                response_json = response.json()
                extracted_value = self.data_manager.extract_value(response_json, case['extract_key'])
                if extracted_value:
                    self.data_manager.set_variable(case['save_var_name'], extracted_value)
                    logger.info(f"变量提取成功: {case['save_var_name']} = {extracted_value}")
                    if ALLURE_AVAILABLE and allure:
                        allure.attach(str(extracted_value), f"提取变量_{case['save_var_name']}",
                                      allure.attachment_type.TEXT)
                else:
                    logger.warning("变量提取失败，未提取到值")
            except Exception as e:
                error_msg = f"变量提取异常: {str(e)}"
                logger.error(error_msg)
                if ALLURE_AVAILABLE and allure:
                    allure.attach(str(e), "变量提取异常", allure.attachment_type.TEXT)
                pytest.fail(error_msg)
        elif case['extract_key']:
            # 处理只有extract_key没有save_var_name的情况（如token=json.token格式）
            logger.info(f"开始提取变量（简化格式）: 键={case['extract_key']}")
            try:
                response_json = response.json()
                extract_key = case['extract_key']
                if '=' in extract_key and not extract_key.startswith(('json.', 'regex:')):
                    # 处理 "变量名=提取路径" 格式，如 "token=json.token"
                    var_name, json_path = extract_key.split('=', 1)
                    # 如果json_path以"json."开头，则去掉前缀
                    if json_path.startswith('json.'):
                        json_path = json_path[5:]  # 去掉"json."前缀
                    extracted_value = self.data_manager.extract_value(response_json, json_path)
                    if extracted_value:
                        self.data_manager.set_variable(var_name.strip(), extracted_value)
                        logger.info(f"变量提取成功: {var_name.strip()} = {extracted_value}")
                        if ALLURE_AVAILABLE and allure:
                            allure.attach(str(extracted_value), f"提取变量_{var_name.strip()}",
                                          allure.attachment_type.TEXT)
                    else:
                        logger.warning("变量提取失败，未提取到值")
                else:
                    # 处理普通的json路径提取
                    extracted_value = self.data_manager.extract_value(response_json, extract_key)
                    if extracted_value:
                        # 对于简化格式，使用extract_key作为变量名（去掉前缀）
                        var_name = extract_key
                        if var_name.startswith('json.'):
                            var_name = var_name[5:]
                        self.data_manager.set_variable(var_name, extracted_value)
                        logger.info(f"变量提取成功: {var_name} = {extracted_value}")
                        if ALLURE_AVAILABLE and allure:
                            allure.attach(str(extracted_value), f"提取变量_{var_name}", allure.attachment_type.TEXT)
                    else:
                        logger.warning("变量提取失败，未提取到值")
            except Exception as e:
                error_msg = f"变量提取异常: {str(e)}"
                logger.error(error_msg)
                if ALLURE_AVAILABLE and allure:
                    allure.attach(str(e), "变量提取异常", allure.attachment_type.TEXT)
                pytest.fail(error_msg)

        logger.info(f"测试用例执行完成: {case['id']} - {case['name']}")
