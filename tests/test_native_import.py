#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""原生 CSV/JSON 导入单元测试。"""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.importers.case_writer import CASE_COLUMNS
from core.importers.native import NativeImportError, import_native_file


class TestNativeImport(unittest.TestCase):
    def test_import_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.csv"
            with open(path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=CASE_COLUMNS)
                writer.writeheader()
                writer.writerow(
                    {
                        "id": "1",
                        "name": "登录",
                        "method": "POST",
                        "url": "/api/login",
                        "headers": "{}",
                        "params": "{}",
                        "body": "{}",
                        "expected_status": "200",
                        "expected_result": "",
                        "extract": "",
                        "validate": "",
                        "priority": "1",
                        "enabled": "1",
                    }
                )
            rows, meta = import_native_file(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(meta["source"], "native")

    def test_import_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            payload = [{"name": "查询", "method": "GET", "url": "/api/user", "expected_status": "200"}]
            path.write_text(json.dumps(payload), encoding="utf-8")
            rows, meta = import_native_file(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(meta["format"], "json")

    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.csv"
            path.write_text("id,name,method,url\n", encoding="utf-8")
            with self.assertRaises(NativeImportError):
                import_native_file(path)


if __name__ == "__main__":
    unittest.main()
