#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    : 
# @File    : test_all_drivers.py
# @Software: PyCharm
"""
统一测试用例执行器，支持Excel和CSV格式
"""

import json

import allure
import pytest

from config.config import Config
from core.assert_handler import AssertHandler
from core.data_handler import DataHandler as GlobalDataHandler
from core.request_handler import RequestHandler
from utils.excel_handler import DataHandler
from utils.logger import logger

# 全局数据处理器
data_handler = GlobalDataHandler()

# 获取所有测试用例
config = Config()
all_test_cases = []
test_files = config.get_all_test_files()
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


@allure.feature("API接口测试")
class TestAllDrivers:

    def setup_method(self):
        """
        测试方法级别的初始化
        """
        logger.debug("初始化测试方法")
        config = Config()
        base_url = config.get_base_url()
        self.request_handler = RequestHandler(base_url=base_url)
        self.assert_handler = AssertHandler()
        self.config = Config()

    @allure.story("所有测试用例执行")
    @pytest.mark.parametrize("case", all_test_cases)
    def test_api_case(self, case):
        """
        执行所有格式的API测试用例

        Args:
            case (dict): 测试用例数据
        """
        logger.info(f"开始执行测试用例: {case['case_id']} - {case['case_name']}")
        with allure.step(f"执行用例: {case['case_id']} - {case['case_name']}"):
            # 替换请求中的变量
            logger.debug("开始处理请求参数中的变量替换")
            url = data_handler.replace_variables(case['url'])

            # 安全地解析JSON字段
            headers_str = data_handler.replace_variables(case['headers'])
            params_str = data_handler.replace_variables(case['params'])
            body_str = data_handler.replace_variables(case['body'])

            headers = {}
            params = {}
            body = {}

            if headers_str and headers_str.strip():
                try:
                    headers = json.loads(headers_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"headers JSON解析失败: {e}, 使用空字典")

            if params_str and params_str.strip():
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"params JSON解析失败: {e}, 使用空字典")

            if body_str and body_str.strip():
                try:
                    body = json.loads(body_str)
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
            # if case['expected_status']:
            #     logger.info(f"执行状态码断言: 期望 {case['expected_status']} 实际 {response.status_code}")
            #     if response:
            #         try:
            #             self.assert_handler.assert_status_code(response.status_code, int(case['expected_status']))
            #             logger.info("状态码断言成功")
            #         except AssertionError as e:
            #             logger.error(f"状态码断言失败: {str(e)}")
            #             pytest.fail(f"状态码断言失败: {str(e)}")
            #         except Exception as e:
            #             logger.error(f"状态码断言异常: {str(e)}")
            #             pytest.fail(f"状态码断言异常: {str(e)}")
            # else:
            #     logger.warning("注意：本次断言为非200状态码断言，若需要则要手动确认是否是在测试反向情况用例")

            # 断言状态码内容
            if case['expected_status']:
                logger.info(f"执行状态码断言: 期望 {case['expected_status']} 实际 {response.status_code}")
            try:
                self.assert_handler.assert_content_contains(response.status_code, case['expected_status'])
            except AssertionError as e:
                logger.error(f"状态码断言失败: {str(e)}")
                pytest.fail(f"状态码断言失败: {str(e)}")
            except Exception as e:
                logger.error(f"状态码断言异常: {str(e)}")
                pytest.fail(f"状态码断言异常: {str(e)}")

            # 如果没有收到有效响应且需要断言内容，则失败
            # 仅当response为None或False时才失败
            if response is None:
                logger.error("请求发送失败，未收到有效响应")
                pytest.fail("请求发送失败，未收到有效响应")

            # 断言响应内容
            if case['expected_content']:
                logger.info(f"执行内容包含断言: 期望包含 '{case['expected_content']}'")
                try:
                    self.assert_handler.assert_content_contains(response, case['expected_content'])
                except AssertionError as e:
                    logger.error(f"内容断言失败: {str(e)}")
                    pytest.fail(f"内容断言失败: {str(e)}")
                except Exception as e:
                    logger.error(f"内容断言异常: {str(e)}")
                    pytest.fail(f"内容断言异常: {str(e)}")

            # 断言JSON值
            if case['json_path'] and case['expected_json_value']:
                logger.info(f"执行JSON值断言: 路径 {case['json_path']}, 期望值 {case['expected_json_value']}")
                try:
                    self.assert_handler.assert_json_value(response, case['json_path'], case['expected_json_value'])
                except AssertionError as e:
                    logger.error(f"JSON值断言失败: {str(e)}")
                    pytest.fail(f"JSON值断言失败: {str(e)}")
                except Exception as e:
                    logger.error(f"JSON值断言异常: {str(e)}")
                    pytest.fail(f"JSON值断言异常: {str(e)}")

            # 提取变量
            if case['extract_key'] and case['save_var_name']:
                logger.info(f"开始提取变量: 键={case['extract_key']}, 保存为={case['save_var_name']}")
                try:
                    response_json = response.json()
                    # 特殊处理类似 "token=json.token" 的格式
                    extract_key = case['extract_key']
                    if '=' in extract_key and not extract_key.startswith(('json.', 'regex:')):
                        # 处理 "变量名=提取路径" 格式，如 "token=json.token"
                        var_name, json_path = extract_key.split('=', 1)
                        # 如果json_path以"json."开头，则去掉前缀
                        if json_path.startswith('json.'):
                            json_path = json_path[5:]  # 去掉"json."前缀
                        extracted_value = data_handler.extract_value(response_json, json_path)
                        if extracted_value:
                            data_handler.set_variable(var_name.strip(), extracted_value)
                            allure.attach(
                                extracted_value,
                                f"提取变量: {var_name.strip()}",
                                allure.attachment_type.TEXT
                            )
                            logger.info(f"变量提取成功: {var_name.strip()} = {extracted_value}")
                        else:
                            logger.warning(f"变量提取失败，未提取到值: {extract_key}")
                    else:
                        # 原有逻辑
                        extracted_value = data_handler.extract_value(response_json, extract_key)
                        if extracted_value:
                            data_handler.set_variable(case['save_var_name'], extracted_value)
                            allure.attach(
                                extracted_value,
                                f"提取变量: {case['save_var_name']}",
                                allure.attachment_type.TEXT
                            )
                            logger.info(f"变量提取成功: {case['save_var_name']} = {extracted_value}")
                        else:
                            logger.warning("变量提取失败，未提取到值")
                except Exception as e:
                    error_msg = f"变量提取异常: {str(e)}"
                    logger.error(error_msg)
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
                        extracted_value = data_handler.extract_value(response_json, json_path)
                        if extracted_value:
                            data_handler.set_variable(var_name.strip(), extracted_value)
                            allure.attach(
                                extracted_value,
                                f"提取变量: {var_name.strip()}",
                                allure.attachment_type.TEXT
                            )
                            logger.info(f"变量提取成功: {var_name.strip()} = {extracted_value}")
                        else:
                            logger.warning(f"变量提取失败，未提取到值: {extract_key}")
                    else:
                        logger.warning(f"提取键格式不正确: {extract_key}")
                except Exception as e:
                    error_msg = f"变量提取异常: {str(e)}"
                    logger.error(error_msg)
                    allure.attach(str(e), "变量提取异常", allure.attachment_type.TEXT)
                    pytest.fail(error_msg)

            # 在Allure报告中显示当前变量状态
            all_vars = data_handler.get_all_variables()
            if all_vars:
                allure.attach(
                    json.dumps(all_vars, ensure_ascii=False, indent=2),
                    "当前变量",
                    allure.attachment_type.JSON
                )

            logger.info(f"测试用例执行完成: {case['case_id']} - {case['case_name']}")
