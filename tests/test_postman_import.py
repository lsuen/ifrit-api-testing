#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Postman 导入单元与 CLI 业务测试。"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.importers.postman import PostmanImporter, PostmanImportError
from core.importers.runner import run_import
from core.cli_manager import CLIManager


POSTMAN_FIXTURE = (
    BASE_DIR / "tests" / "fixtures" / "postman" / "ifrit_address_smoke.postman_collection.json"
)


class TestPostmanImporter(unittest.TestCase):
    def test_convert_fixture_rows(self):
        importer = PostmanImporter(str(POSTMAN_FIXTURE))
        rows, meta = importer.convert()
        self.assertEqual(meta["case_count"], 3)
        self.assertEqual(rows[0]["method"], "GET")
        self.assertEqual(rows[0]["url"], "/api/test")
        self.assertEqual(rows[0]["expected_status"], "200")
        self.assertEqual(rows[1]["url"], "/api/login")
        self.assertIn("test", rows[1]["body"])
        self.assertEqual(rows[2]["name"], "地址 - 地址列表")
        self.assertEqual(rows[2]["expected_result"], "success")

    def test_write_csv_readable(self):
        importer = PostmanImporter(str(POSTMAN_FIXTURE))
        rows, _ = importer.convert()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.csv"
            PostmanImporter.write_csv(rows, out)
            with open(out, "r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                saved = list(reader)
            self.assertEqual(len(saved), 3)
            self.assertEqual(saved[0]["url"], "/api/test")

    def test_invalid_schema_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            tmp.write('{"info": {"schema": "v1"}, "item": []}')
            bad_path = tmp.name
        try:
            with self.assertRaises(PostmanImportError):
                PostmanImporter(bad_path).convert()
        finally:
            os.unlink(bad_path)

    def test_dry_run_via_runner(self):
        class Args:
            import_file = str(POSTMAN_FIXTURE)
            import_format = "postman"
            import_suite = "manual"
            import_output = None
            import_dry_run = True
            import_ai_enhance = False

        self.assertEqual(run_import(Args()), 0)


class TestPostmanImportCLI(unittest.TestCase):
    def test_cli_import_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_csv = Path(tmp) / "imported.csv"
            cmd = [
                sys.executable,
                str(BASE_DIR / "main.py"),
                "--import",
                str(POSTMAN_FIXTURE),
                "--import-format",
                "postman",
                "--import-suite",
                "manual",
                "--import-output",
                str(out_csv),
            ]
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("[IFRIT] 导入完成", result.stdout)
            self.assertTrue(out_csv.is_file())
            with open(out_csv, "r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)

    def test_cli_import_then_smoke_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_csv = Path(tmp) / "imported.csv"
            import_cmd = [
                sys.executable,
                str(BASE_DIR / "main.py"),
                "--import",
                str(POSTMAN_FIXTURE),
                "--import-output",
                str(out_csv),
            ]
            import_result = subprocess.run(
                import_cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(import_result.returncode, 0, import_result.stderr)

            run_cmd = [
                sys.executable,
                str(BASE_DIR / "main.py"),
                "--file",
                str(out_csv),
                "--global-auth",
            ]
            run_result = subprocess.run(
                run_cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            self.assertEqual(run_result.returncode, 0, run_result.stdout + run_result.stderr)
            self.assertIn("[IFRIT] PASS", run_result.stdout)

    def test_cli_import_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "imported.json"
            cmd = [
                sys.executable,
                str(BASE_DIR / "main.py"),
                "--import",
                str(POSTMAN_FIXTURE),
                "--import-output",
                str(out_json),
                "--import-output-format",
                "json",
            ]
            result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out_json.is_file())
            with open(out_json, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(len(data), 3)

    def test_cli_preview_json(self):
        cmd = [
            sys.executable,
            str(BASE_DIR / "main.py"),
            "--import",
            str(POSTMAN_FIXTURE),
            "--import-preview-only",
        ]
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0)
        self.assertIn("IMPORT_PREVIEW_JSON=", result.stdout)

    def test_cli_manager_has_import_args(self):
        parser = CLIManager().parser
        args = parser.parse_args(
            [
                "--import",
                str(POSTMAN_FIXTURE),
                "--import-dry-run",
            ]
        )
        self.assertEqual(args.import_file, str(POSTMAN_FIXTURE))
        self.assertTrue(args.import_dry_run)


if __name__ == "__main__":
    unittest.main()
