#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：Agent ReAct 与 Skill 注册表单元测试
创建时间：2026-06-02
"""
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.actions.parse_document import ParseDocumentAction
from agent.react.loop import ReActLoop
from agent.skills.registry import get_actions, list_skills


class TestAgentSkills(unittest.TestCase):
    """Agent Skill 与 Action 测试。"""

    def test_list_skills(self):
        skills = list_skills()
        self.assertIn("case_generation", skills)
        self.assertIn("parse_only", skills)

    def test_parse_document_action(self):
        context = {
            "input_doc": os.path.join(BASE_DIR, "api_docs", "apispec_1.json"),
            "endpoints": ["/api/test"],
        }
        result = ParseDocumentAction().run(context)
        self.assertEqual(len(result["apis"]), 1)
        self.assertEqual(result["apis"][0]["path"], "/api/test")
        self.assertEqual(result["apis"][0]["method"], "GET")

    def test_react_parse_only_skill(self):
        loop = ReActLoop(get_actions("parse_only"))
        context = loop.run(
            {
                "input_doc": os.path.join(BASE_DIR, "api_docs", "apispec_1.json"),
                "endpoints": ["/api/test"],
            }
        )
        self.assertIn("apis", context)


if __name__ == "__main__":
    unittest.main()
