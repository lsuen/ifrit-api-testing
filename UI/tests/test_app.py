#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web UI 单元测试。"""
import sys
import unittest
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UI_DIR))

from app import app, init_app_config
from services.cli_runner import build_ai_generate_command, build_test_command
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


if __name__ == "__main__":
    unittest.main()
