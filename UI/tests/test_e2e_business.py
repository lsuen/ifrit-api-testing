#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UI 业务端到端测试（需 UI 服务运行在 5001）。"""
import json
import sys
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

UI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UI_DIR))

BASE = "http://127.0.0.1:5001"
TIMEOUT = 120


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_form(path: str, fields: dict) -> dict:
    from urllib.parse import urlencode

    data = urlencode(fields).encode("utf-8")
    req = Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urlopen(f"{BASE}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _wait_process(process_id: str, timeout: float = TIMEOUT) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        last = _get(f"/api/process/{process_id}/status")
        if last.get("status") in ("completed", "failed", "cancelled"):
            return last
        time.sleep(1)
    raise TimeoutError(f"进程 {process_id} 超时，最后状态: {last}")


class TestUIBusinessE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with urlopen(f"{BASE}/api/overview", timeout=5):
                pass
        except (URLError, OSError) as error:
            raise unittest.SkipTest(f"UI 未启动 ({BASE}): {error}") from error

    def test_overview_has_real_stats(self):
        data = _get("/api/overview")
        self.assertIn("stats", data)
        stats = data["stats"]
        self.assertIsNotNone(stats.get("smoke_cases"))
        self.assertGreaterEqual(stats["smoke_cases"], 2)

    def test_execute_smoke_via_api(self):
        res = _post(
            "/api/execute",
            {
                "params": {
                    "file": "fixtures/smoke/csv/api_test_smoke.csv",
                    "suite": "smoke",
                    "generate_report": True,
                }
            },
        )
        self.assertIn("process_id", res)
        status = _wait_process(res["process_id"])
        self.assertEqual(status["status"], "completed", status.get("command"))

    def test_execute_ai_business_via_api(self):
        res = _post(
            "/api/execute",
            {
                "params": {
                    "file": "fixtures/ai/csv/ai_address_business.csv",
                    "suite": "ai",
                    "global_auth": True,
                    "generate_report": True,
                }
            },
        )
        self.assertIn("process_id", res)
        status = _wait_process(res["process_id"])
        self.assertEqual(status["status"], "completed", status.get("command"))

    def test_ai_chat_doc_via_api(self):
        res = _post(
            "/api/ai/chat",
            {"commands": ["doc", "api_docs/apispec_1.json"]},
        )
        self.assertIn("process_id", res)
        status = _wait_process(res["process_id"], timeout=60)
        self.assertEqual(status["status"], "completed", status.get("command"))

    def test_import_postman_dry_run_via_api(self):
        res = _post_form(
            "/api/import",
            {
                "source_path": "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json",
                "suite": "manual",
                "dry_run": "1",
            },
        )
        self.assertIn("process_id", res)
        status = _wait_process(res["process_id"], timeout=60)
        self.assertEqual(status["status"], "completed", status.get("command"))
        self.assertIn("--import-dry-run", status.get("command", ""))


if __name__ == "__main__":
    unittest.main()
