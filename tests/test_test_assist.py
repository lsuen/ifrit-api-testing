#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 AI 辅助分析单元测试。"""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.test_assist import (
    ASSIST_MARKER,
    _extract_failure_snippets,
    analyze_test_output,
    save_assist_report,
)


class TestTestAssist(unittest.TestCase):
    def test_extract_failure_snippets(self):
        text = "PASSED ok\nFAILED test_login\nAssertionError: 401"
        lines = _extract_failure_snippets(text, "")
        self.assertTrue(any("FAILED" in ln for ln in lines))

    def test_analyze_no_failures(self):
        result = analyze_test_output("", "")
        self.assertIn("无需", result["summary"])

    @patch("core.test_assist.AIConfig")
    @patch("core.test_assist.AIClient")
    def test_analyze_with_llm(self, mock_client_cls, mock_config_cls):
        mock_config_cls.return_value.validate_config.return_value = True
        mock_config_cls.return_value.get_openai_config.return_value = {}
        client = MagicMock()
        client.complete.return_value = json.dumps(
            {
                "summary": "登录失败",
                "diagnosis": [{"case": "login", "detail": "token 过期", "severity": "high"}],
                "suggestions": [{"title": "刷新 token", "action": "重新登录", "retain_default": False}],
                "save_hint": "可保存到 reports",
            },
            ensure_ascii=False,
        )
        mock_client_cls.return_value = client

        result = analyze_test_output("FAILED test_login", "", suite="smoke")
        self.assertEqual(result["summary"], "登录失败")
        self.assertEqual(result["retain_decision"], "user")

    def test_save_assist_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_assist_report(tmp, "run123", {"summary": "x"})
            full = os.path.join(tmp, path.replace("/", os.sep))
            self.assertTrue(os.path.isfile(full))
            with open(full, encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data["summary"], "x")

    def test_assist_marker_constant(self):
        self.assertIn("TEST_ASSIST_JSON", ASSIST_MARKER)


if __name__ == "__main__":
    unittest.main()
