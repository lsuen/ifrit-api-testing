#!/usr/bin/env python 
# -*- coding: utf-8 -*-
# @Time    : 2025/9/18 下午1:31
# @Author  : sunwl
# @Site    : 
# @File    : test_executor.py
# @Software: PyCharm
# core/test_executor.py
import json
import allure
import pytest
from utils.logger import logger


class TestExecutor:
    def __init__(self, request_handler, data_handler, assert_handler):
        self.request_handler = request_handler
        self.data_handler = data_handler
        self.assert_handler = assert_handler

    def execute_test_case(self, case):
        """
        执行单个测试用例的公共方法

        Args:
            case (dict): 测试用例数据
        """
        logger.info(f"开始执行测试用例: {case['case_id']} - {case['case_name']}")

        # 使用allure（如果可用）
        if hasattr(allure, 'step'):
            with allure.step(f"执行用例: {case['case_id']} - {case['case_name']}"):
                return self._execute_case_logic(case)
        else:
            return self._execute_case_logic(case)

    def _execute_case_logic(self, case):
        """
        实际执行测试用例的逻辑

        Args:
            case (dict): 测试用例数据
        """
        # 替换请求中的变量
        logger.debug("开始处理请求参数中的变量替换")
        url = self.data_handler.replace_variables(case['url'])

        # 安全地解析JSON字段
        headers_str = self.data_handler.replace_variables(case['headers'])
        params_str = self.data_handler.replace_variables(case['params'])
        body_str = self.data_handler.replace_variables(case['body'])

        headers = {}
        params = {}
        body = {}

        if headers_str and headers_str.strip():
            try:
                headers = json.loads(headers_str)
            except json.JSONDecodeError as e:
                logger.warning(f"headers JSON解析失败: {e}, 使用空字典")

        # 获取Content-Type
        content_type = headers.get('Content-Type', '').lower() if isinstance(headers, dict) else ''

        if params_str and params_str.strip():
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as e:
                logger.warning(f"params JSON解析失败: {e}, 使用空字典")

        if body_str and body_str.strip():
            # 根据Content-Type判断是否需要解析JSON
            if 'text/plain' in content_type:
                # text/plain类型，body作为纯文本处理
                body = body_str
                logger.debug("Content-Type为text/plain，body作为纯文本处理")
            elif 'application/x-www-form-urlencoded' in content_type:
                # form类型，body作为字符串处理
                body = body_str
                logger.debug("Content-Type为application/x-www-form-urlencoded，body作为字符串处理")
            else:
                # 默认或其他类型，尝试解析为JSON
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"body JSON解析失败: {e}, 使用空字典")

        logger.debug("请求参数变量替换完成")

        # 发送请求
        logger.info(f"发送 {case['method']} 请求到 {url}")
        # 根据Content-Type决定使用哪个参数发送body
        if 'text/plain' in content_type and isinstance(body, str):
            response = self.request_handler.send_request(
                method=case['method'],
                url=url,
                headers=headers,
                params=params,
                plain_text=body
            )
        else:
            response = self.request_handler.send_request(
                method=case['method'],
                url=url,
                headers=headers,
                params=params,
                json_data=body
            )

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
                    extracted_value = self.data_handler.extract_value(response_json, json_path)
                    if isinstance(extracted_value, dict):
                        # 多值提取结果，分别存储每个变量
                        for key, value in extracted_value.items():
                            self.data_handler.set_variable(key, value)
                            # 使用allure（如果可用）
                            if hasattr(allure, 'attach'):
                                allure.attach(
                                    value,
                                    f"提取变量: {key}",
                                    allure.attachment_type.TEXT
                                )
                            logger.info(f"变量提取成功: {key} = {value}")
                    elif extracted_value:
                        self.data_handler.set_variable(var_name.strip(), extracted_value)
                        # 使用allure（如果可用）
                        if hasattr(allure, 'attach'):
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
                    extracted_value = self.data_handler.extract_value(response_json, extract_key)
                    if isinstance(extracted_value, dict):
                        # 多值提取结果，分别存储每个变量
                        for key, value in extracted_value.items():
                            self.data_handler.set_variable(key, value)
                            # 使用allure（如果可用）
                            if hasattr(allure, 'attach'):
                                allure.attach(
                                    value,
                                    f"提取变量: {key}",
                                    allure.attachment_type.TEXT
                                )
                            logger.info(f"变量提取成功: {key} = {value}")
                    elif extracted_value:
                        self.data_handler.set_variable(case['save_var_name'], extracted_value)
                        # 使用allure（如果可用）
                        if hasattr(allure, 'attach'):
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
                # 使用allure（如果可用）
                if hasattr(allure, 'attach'):
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
                    extracted_value = self.data_handler.extract_value(response_json, json_path)
                    if isinstance(extracted_value, dict):
                        # 多值提取结果，分别存储每个变量
                        for key, value in extracted_value.items():
                            self.data_handler.set_variable(key, value)
                            # 使用allure（如果可用）
                            if hasattr(allure, 'attach'):
                                allure.attach(
                                    value,
                                    f"提取变量: {key}",
                                    allure.attachment_type.TEXT
                                )
                            logger.info(f"变量提取成功: {key} = {value}")
                    elif extracted_value:
                        self.data_handler.set_variable(var_name.strip(), extracted_value)
                        # 使用allure（如果可用）
                        if hasattr(allure, 'attach'):
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
                # 使用allure（如果可用）
                if hasattr(allure, 'attach'):
                    allure.attach(str(e), "变量提取异常", allure.attachment_type.TEXT)
                pytest.fail(error_msg)

        # 在Allure报告中显示当前变量状态（如果可用）
        all_vars = self.data_handler.get_all_variables()
        if all_vars and hasattr(allure, 'attach'):
            allure.attach(
                json.dumps(all_vars, ensure_ascii=False, indent=2),
                "当前变量",
                allure.attachment_type.JSON
            )

        logger.info(f"测试用例执行完成: {case['case_id']} - {case['case_name']}")
