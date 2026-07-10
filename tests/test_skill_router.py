#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 路由 Function Calling 单元测试。"""
import os
import sys
import unittest
from unittest.mock import MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 避免 agent/__init__.py 拉取 pandas 等重依赖
import types

if "agent" not in sys.modules:
    _agent_pkg = types.ModuleType("agent")
    _agent_pkg.__path__ = [os.path.join(BASE_DIR, "agent")]
    sys.modules["agent"] = _agent_pkg

from agent.skills.router import (
    SELECT_SKILL_TOOL_NAME,
    _rule_based_route,
    build_skill_tool_schema,
    route_skill,
)


class TestSkillRouter(unittest.TestCase):
    def test_build_skill_tool_schema_enum(self):
        schema = build_skill_tool_schema(["case_generation", "parse_only"])
        fn = schema[0]["function"]
        self.assertEqual(fn["name"], SELECT_SKILL_TOOL_NAME)
        self.assertIn("case_generation", fn["parameters"]["properties"]["skill_name"]["enum"])

    def test_rule_based_url(self):
        routed = _rule_based_route({"input_url": "http://example.com/spec.json"})
        self.assertEqual(routed["skill_name"], "doc_url_generation")
        self.assertEqual(routed["source"], "rule")

    def test_rule_based_single_endpoint(self):
        routed = _rule_based_route({"endpoints": ["/api/foo"]})
        self.assertEqual(routed["skill_name"], "parse_only")

    def test_function_calling_route(self):
        client = MagicMock()
        client.chat_with_tools.return_value = {
            "tool_calls": [
                {
                    "name": SELECT_SKILL_TOOL_NAME,
                    "arguments": {
                        "skill_name": "case_generation",
                        "reason": "本地文档生成",
                        "confidence": 0.9,
                    },
                }
            ]
        }
        routed = route_skill(
            client,
            {"input_doc": "api_docs/apispec_1.json"},
            event_sink=lambda _: None,
        )
        self.assertEqual(routed["skill_name"], "case_generation")
        self.assertEqual(routed["source"], "function_calling")
        client.chat_with_tools.assert_called_once()

    def test_fallback_on_llm_error(self):
        client = MagicMock()
        client.chat_with_tools.side_effect = RuntimeError("LLM down")
        routed = route_skill(
            client,
            {"input_doc": "api_docs/apispec_1.json"},
            event_sink=lambda _: None,
        )
        self.assertEqual(routed["skill_name"], "case_generation")
        self.assertEqual(routed["source"], "rule")


if __name__ == "__main__":
    unittest.main()
