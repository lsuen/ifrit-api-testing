#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web UI 单元测试。"""
import sys
import unittest
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UI_DIR))

from app import app, init_app_config
from services.cli_runner import (
    build_ai_chat_command,
    build_ai_generate_command,
    build_import_command,
    build_test_command,
)
from services.config_loader import load_config


class TestUIPlatform(unittest.TestCase):
    def setUp(self):
        init_app_config()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("仪表盘".encode(), response.data)

    def test_execute_page(self):
        self.assertEqual(self.client.get("/execute").status_code, 200)

    def test_ai_page(self):
        self.assertEqual(self.client.get("/ai").status_code, 200)

    def test_reports_page(self):
        self.assertEqual(self.client.get("/reports").status_code, 200)

    def test_advanced_page(self):
        self.assertEqual(self.client.get("/advanced").status_code, 200)

    def test_import_page(self):
        response = self.client.get("/import")
        self.assertEqual(response.status_code, 200)
        self.assertIn("导入中心".encode(), response.data)

    def test_about_page(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn("关于".encode(), response.data)

    def test_skills_page(self):
        response = self.client.get("/skills")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Skill 管理".encode(), response.data)

    def test_console_page(self):
        response = self.client.get("/console")
        self.assertEqual(response.status_code, 200)
        self.assertIn("控制台".encode(), response.data)

    def test_knowledge_page(self):
        response = self.client.get("/knowledge")
        self.assertEqual(response.status_code, 200)
        self.assertIn("知识库".encode(), response.data)

    def test_settings_page(self):
        response = self.client.get("/settings")
        self.assertEqual(response.status_code, 200)
        self.assertIn("设置".encode(), response.data)

    def test_api_settings(self):
        response = self.client.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("ui_prefs", data)
        self.assertIn("env_options", data)

    def test_api_settings_health(self):
        response = self.client.post("/api/settings/health", json={"ping_llm": False})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("checks", data)
        self.assertIn("ready", data)

    def test_api_settings_prefs(self):
        response = self.client.post(
            "/api/settings/prefs",
            json={"rag_default_on": True, "auto_ingest_rag": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("success"))

    def test_dashboard_has_pipeline(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("一键流水线".encode(), response.data)
        self.assertIn("pipelineSmokeBtn".encode(), response.data)

    def test_sidebar_settings_link(self):
        response = self.client.get("/execute")
        self.assertIn("/settings".encode(), response.data)
        self.assertIn("新手入门".encode(), response.data)

    def test_agent_page(self):
        response = self.client.get("/agent")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Agent 对话".encode(), response.data)

    def test_api_agent_plan_greeting(self):
        response = self.client.post("/api/agent/plan", json={"message": "你好", "form": {}})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("intent"), "converse")
        self.assertTrue(data.get("reply"))
        self.assertEqual(data.get("steps"), [])

    def test_api_agent_plan_smoke(self):
        response = self.client.post("/api/agent/plan", json={"message": "跑冒烟测试", "form": {}})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("intent"), "execute_smoke")
        self.assertTrue(data.get("steps"))

    def test_api_agent_context(self):
        response = self.client.get("/api/agent/context")
        self.assertEqual(response.status_code, 200)
        self.assertIn("smoke_file", response.get_json())

    def test_dashboard_import_pipeline_button(self):
        response = self.client.get("/")
        self.assertIn("pipelineImportBtn".encode(), response.data)
        self.assertIn("导入→执行".encode(), response.data)

    def test_api_knowledge_stats(self):
        response = self.client.get("/api/knowledge/stats")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("success"))

    def test_api_cases_catalog(self):
        response = self.client.get("/api/cases/catalog")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("success"))

    def test_api_console_policy(self):
        response = self.client.get("/api/console/policy")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("quick_recipes", data.get("policy", {}))

    def test_api_console_validate_block(self):
        response = self.client.post("/api/console/validate", json={"mode": "cli", "line": "rm -rf"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data.get("ok"))

    def test_api_console_validate_ok(self):
        response = self.client.post("/api/console/validate", json={"mode": "cli", "line": "--help"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("ok"))

    def test_api_test_assist_missing_log(self):
        response = self.client.post("/api/test/assist", json={})
        self.assertEqual(response.status_code, 400)

    def test_api_skills_builtin(self):
        response = self.client.get("/api/skills/builtin")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertTrue(any(s["name"] == "case_generation" for s in data.get("skills", [])))

    def test_api_skills_catalog(self):
        response = self.client.get("/api/skills/catalog")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json().get("success"))

    def test_api_about_info(self):
        response = self.client.get("/api/about/info")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("name", data)
        self.assertIn("stats", data)

    def test_api_about_manual(self):
        response = self.client.get("/api/about/manual")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("用户详细使用手册", data.get("source", ""))

    def test_api_about_cli(self):
        response = self.client.get("/api/about/cli")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertTrue(len(data.get("recipes", [])) >= 1)

    def test_api_import_dry_run(self):
        sample = (
            load_config()["ifrit"]["root_path_resolved"]
            / "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json"
        )
        self.assertTrue(sample.is_file())
        response = self.client.post(
            "/api/import",
            data={
                "source_path": "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json",
                "suite": "manual",
                "dry_run": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("process_id", data)
        self.assertIn("--import-dry-run", data["command"])

    def test_build_import_command(self):
        config = load_config()
        cmd = build_import_command(
            config,
            {
                "import_file": "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json",
                "suite": "manual",
                "format": "postman",
                "output_format": "json",
            },
        )
        joined = " ".join(cmd)
        self.assertIn("--import", joined)
        self.assertIn("--import-format postman", joined)
        self.assertIn("--import-suite manual", joined)
        self.assertIn("--import-output-format json", joined)

    def test_import_preview_api(self):
        response = self.client.post(
            "/api/import/preview",
            data={"source_path": "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("case_count"), 3)

    def test_api_overview(self):
        response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("stats", data)

    def test_build_test_command_with_auth(self):
        config = load_config()
        cmd = build_test_command(
            config,
            {"file": "fixtures/smoke/csv/api_test_smoke.csv", "global_auth": True, "generate_report": True},
        )
        joined = " ".join(cmd)
        self.assertIn("--global-auth", joined)
        self.assertIn("--generate-report", joined)

    def test_build_test_command_with_assist(self):
        config = load_config()
        cmd = build_test_command(
            config,
            {"suite": "smoke", "test_assist": True},
        )
        self.assertIn("--test-assist", cmd)

    def test_build_ai_auto_skill_flags(self):
        config = load_config()
        cmd = build_ai_generate_command(
            config,
            {
                "input_doc": "api_docs/apispec_1.json",
                "no_auto_skill": True,
                "skill_hint": "鉴权发现",
            },
        )
        joined = " ".join(cmd)
        self.assertIn("--no-auto-skill", joined)
        self.assertIn("--skill-hint", joined)

    def test_build_ai_url_command(self):
        config = load_config()
        cmd = build_ai_generate_command(
            config,
            {
                "input_url": "http://example.com/spec.json",
                "endpoints": ["/api/address"],
                "format": "csv",
            },
        )
        joined = " ".join(cmd)
        self.assertIn("--input-url", joined)
        self.assertIn("--swagger-endpoint", joined)

    def test_reports_view_redirect(self):
        response = self.client.get("/reports/view/test_run_123", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/reports/view/test_run_123/", response.headers.get("Location", ""))

    def test_api_reports_delete_invalid(self):
        response = self.client.delete("/api/reports/run/../../etc")
        self.assertIn(response.status_code, (404, 400))
        config = load_config()
        cmd = build_ai_chat_command(config, ["doc", "api_docs/apispec_1.json", "generate"])
        self.assertIn("--chat", cmd)
        chat_idx = cmd.index("--chat")
        self.assertEqual(cmd[chat_idx + 1], "doc")
        self.assertNotIn("--", cmd[chat_idx + 1 :])


if __name__ == "__main__":
    unittest.main()
