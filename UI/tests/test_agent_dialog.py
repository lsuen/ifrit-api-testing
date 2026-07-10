#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Agent 对话服务单元测试。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "UI"
sys.path.insert(0, str(UI_DIR))

from services.agent_dialog_service import _match_intent, build_agent_plan, get_agent_context
from services.config_loader import load_config


class TestAgentDialog(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_match_intent_smoke(self):
        self.assertEqual(_match_intent("跑冒烟测试"), "execute_smoke")

    def test_match_intent_import_execute(self):
        self.assertEqual(_match_intent("导入 Postman 并执行"), "import_execute")

    def test_match_intent_cli(self):
        self.assertEqual(_match_intent("--file fixtures/smoke/csv/api_test_smoke.csv"), "cli")

    def test_match_intent_chat(self):
        self.assertEqual(_match_intent("doc api_docs/apispec_1.json generate"), "chat")

    def test_build_plan_generate(self):
        ctx = get_agent_context(self.config)
        if not ctx.get("default_doc"):
            self.skipTest("无 api_docs 文档")
        plan = build_agent_plan(self.config, {"message": "生成 /api/address 用例", "form": {}})
        self.assertEqual(plan["intent"], "generate")
        self.assertTrue(plan["steps"])
        self.assertEqual(plan["steps"][0]["type"], "generate")

    def test_build_plan_import_execute(self):
        ctx = get_agent_context(self.config)
        if not ctx.get("sample_import"):
            self.skipTest("无 Postman 样例")
        plan = build_agent_plan(self.config, {"message": "导入并执行", "form": {}})
        self.assertEqual(plan["intent"], "import_execute")
        types = [s["type"] for s in plan["steps"]]
        self.assertIn("import", types)
        self.assertIn("execute", types)


if __name__ == "__main__":
    unittest.main()
