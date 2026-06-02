#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：测试用例执行器，统一执行逻辑与 Allure 报告步骤
创建时间：2025-09-18
"""
import json
import logging

import pytest

from core.allure_helper import AllureReporter

logger = logging.getLogger(__name__)


class TestCaseExecutor:
    """API 测试用例执行器（避免与 pytest 收集冲突）。"""

    __test__ = False  # 防止 pytest 误收集

    def __init__(self, request_handler, data_handler, assert_handler, auth_manager=None):
        self.request_handler = request_handler
        self.data_handler = data_handler
        self.assert_handler = assert_handler
        self.auth_manager = auth_manager

    def execute_test_case(self, case):
        """执行单个测试用例。"""
        suite = case.get("_suite", "manual")
        data_format = case.get("_format", "csv")
        AllureReporter.set_case_labels(case, suite, data_format)

        logger.info("开始执行测试用例: %s - %s", case["case_id"], case["case_name"])
        return self._execute_case_logic(case)

    def _execute_case_logic(self, case):
        url = self.data_handler.replace_variables(case["url"])
        headers_str = self.data_handler.replace_variables(case["headers"])
        params_str = self.data_handler.replace_variables(case["params"])
        body_str = self.data_handler.replace_variables(case["body"])

        headers = {}
        params = {}
        body = {}

        if headers_str and headers_str.strip():
            try:
                headers = json.loads(headers_str)
            except json.JSONDecodeError as error:
                logger.warning("headers JSON解析失败: %s, 使用空字典", error)

        content_type = headers.get("Content-Type", "").lower() if isinstance(headers, dict) else ""

        if params_str and params_str.strip():
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as error:
                logger.warning("params JSON解析失败: %s, 使用空字典", error)

        if body_str and body_str.strip():
            if "text/plain" in content_type:
                body = body_str
            elif "application/x-www-form-urlencoded" in content_type:
                body = body_str
            else:
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError as error:
                    logger.warning("body JSON解析失败: %s, 使用空字典", error)

        if self.auth_manager:
            headers = self.auth_manager.apply_to_headers(headers, url)
            if isinstance(body, dict):
                body = self.auth_manager.apply_to_body(body, url)

        logger.info("发送 %s 请求到 %s", case["method"], url)
        if "text/plain" in content_type and isinstance(body, str):
            response = self.request_handler.send_request(
                method=case["method"],
                url=url,
                headers=headers,
                params=params,
                plain_text=body,
            )
        else:
            response = self.request_handler.send_request(
                method=case["method"],
                url=url,
                headers=headers,
                params=params,
                json_data=body,
            )

        if response is None:
            logger.error("请求发送失败，未收到有效响应")
            pytest.fail("请求发送失败，未收到有效响应")

        if case["expected_status"]:
            expected = int(case["expected_status"])
            AllureReporter.step_assertion(
                "断言状态码",
                f"期望 {expected}，实际 {response.status_code}",
            )
            try:
                self.assert_handler.assert_status_code(response, expected)
            except AssertionError as error:
                logger.error("状态码断言失败: %s", error)
                if (
                    self.auth_manager
                    and self.auth_manager.handle_auth_failure(response.status_code)
                ):
                    logger.info("鉴权已恢复，请重新运行用例")
                pytest.fail(f"状态码断言失败: {error}")
            except Exception as error:
                logger.error("状态码断言异常: %s", error)
                pytest.fail(f"状态码断言异常: {error}")

        if case["expected_content"]:
            AllureReporter.step_assertion(
                "断言响应内容",
                f"期望包含: {case['expected_content']}",
            )
            try:
                self.assert_handler.assert_content_contains(response, case["expected_content"])
            except AssertionError as error:
                logger.error("内容断言失败: %s", error)
                pytest.fail(f"内容断言失败: {error}")

        if case["json_path"] and case["expected_json_value"]:
            AllureReporter.step_assertion(
                "断言 JSON 值",
                f"路径 {case['json_path']} = {case['expected_json_value']}",
            )
            try:
                self.assert_handler.assert_json_value(
                    response, case["json_path"], case["expected_json_value"]
                )
            except AssertionError as error:
                logger.error("JSON值断言失败: %s", error)
                pytest.fail(f"JSON值断言失败: {error}")

        extracted = self._extract_variables(case, response)
        if extracted:
            AllureReporter.attach_extracted_variables(extracted)

        logger.info("测试用例执行完成: %s - %s", case["case_id"], case["case_name"])

    def _extract_variables(self, case, response) -> dict:
        """提取变量并写入 data_handler，返回本次提取结果。"""
        extract_key = case.get("extract_key") or ""
        if not extract_key:
            return {}

        extracted = {}
        try:
            response_json = response.json()
        except Exception as error:
            error_msg = f"变量提取失败（响应非 JSON）: {error}"
            logger.error(error_msg)
            AllureReporter.attach_error("变量提取异常", error_msg)
            pytest.fail(error_msg)
            return {}

        if "=" in extract_key and not extract_key.startswith(("json.", "regex:")):
            var_name, json_path = extract_key.split("=", 1)
            if json_path.startswith("json."):
                json_path = json_path[5:]
            value = self.data_handler.extract_value(response_json, json_path)
            if isinstance(value, dict):
                for key, item_value in value.items():
                    self.data_handler.set_variable(key, item_value)
                    extracted[key] = item_value
            elif value:
                name = var_name.strip()
                self.data_handler.set_variable(name, value)
                extracted[name] = value
        else:
            save_name = case.get("save_var_name") or "extracted"
            value = self.data_handler.extract_value(response_json, extract_key)
            if isinstance(value, dict):
                for key, item_value in value.items():
                    self.data_handler.set_variable(key, item_value)
                    extracted[key] = item_value
            elif value:
                self.data_handler.set_variable(save_name, value)
                extracted[save_name] = value

        return extracted


# 向后兼容别名
TestExecutor = TestCaseExecutor
