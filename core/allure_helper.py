#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：Allure 报告附件与步骤的统一封装，避免重复与层级混乱
创建时间：2026-06-02
"""
import json
from typing import Any, Dict, Optional

try:
    import allure

    ALLURE_AVAILABLE = True
except ImportError:
    allure = None
    ALLURE_AVAILABLE = False


class AllureReporter:
    """Allure 报告辅助类。"""

    @staticmethod
    def is_available() -> bool:
        return ALLURE_AVAILABLE and allure is not None

    @staticmethod
    def set_case_labels(case: dict, suite: str, data_format: str) -> None:
        """设置用例动态标签与标题。"""
        if not AllureReporter.is_available():
            return

        case_id = case.get("case_id", "")
        case_name = case.get("case_name", "")
        method = case.get("method", "")
        url = case.get("url", "")

        allure.dynamic.epic("API 自动化测试")
        allure.dynamic.feature(f"{suite} · {data_format.upper()}")
        allure.dynamic.story(f"{method} {url}")
        allure.dynamic.title(f"{case_id} · {case_name}")
        for tag in (suite, data_format.upper(), method):
            if tag:
                allure.dynamic.tag(tag)

    @staticmethod
    def step_request(
        method: str,
        url: str,
        headers: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        body: Any,
        curl_command: str,
    ) -> None:
        """记录请求步骤（合并为少量附件）。"""
        if not AllureReporter.is_available():
            return

        with allure.step(f"请求 {method} {url}"):
            allure.attach(curl_command, "cURL", allure.attachment_type.TEXT)
            payload = {
                "method": method,
                "url": url,
                "headers": headers or {},
                "params": params or {},
                "body": body,
            }
            allure.attach(
                json.dumps(payload, ensure_ascii=False, indent=2),
                "请求详情",
                allure.attachment_type.JSON,
            )

    @staticmethod
    def step_response(response) -> None:
        """记录响应步骤。"""
        if not AllureReporter.is_available() or response is None:
            return

        elapsed = response.elapsed.total_seconds() if hasattr(response, "elapsed") else 0
        with allure.step(f"响应 {response.status_code} ({elapsed:.3f}s)"):
            summary = {
                "status_code": response.status_code,
                "elapsed_seconds": elapsed,
                "headers": dict(response.headers),
            }
            allure.attach(
                json.dumps(summary, ensure_ascii=False, indent=2),
                "响应概要",
                allure.attachment_type.JSON,
            )
            body_text = response.text or ""
            if len(body_text) > 8000:
                body_text = body_text[:8000] + "\n... (truncated)"
            allure.attach(body_text, "响应体", allure.attachment_type.TEXT)

    @staticmethod
    def step_assertion(name: str, detail: str) -> None:
        """记录断言步骤。"""
        if not AllureReporter.is_available():
            return
        with allure.step(name):
            if detail:
                allure.attach(detail, "断言详情", allure.attachment_type.TEXT)

    @staticmethod
    def attach_extracted_variables(variables: Dict[str, str]) -> None:
        """合并记录提取的变量。"""
        if not AllureReporter.is_available() or not variables:
            return
        with allure.step("提取变量"):
            allure.attach(
                json.dumps(variables, ensure_ascii=False, indent=2),
                "变量",
                allure.attachment_type.JSON,
            )

    @staticmethod
    def attach_error(title: str, message: str) -> None:
        if not AllureReporter.is_available():
            return
        allure.attach(message, title, allure.attachment_type.TEXT)
