#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI 交互模式测试。"""
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.pipeline.chat import AIChatSession


class TestAIChat(unittest.TestCase):
    def test_single_line_show_and_help(self):
        session = AIChatSession()
        self.assertEqual(session.run(["help"]), 0)
        self.assertEqual(session.run(["doc", "api_docs/apispec_1.json", "show"]), 0)
        self.assertEqual(session.state["input_doc"], "api_docs/apispec_1.json")

    def test_generate_requires_doc(self):
        session = AIChatSession()
        self.assertEqual(session.run(["generate"]), 1)


if __name__ == "__main__":
    unittest.main()
