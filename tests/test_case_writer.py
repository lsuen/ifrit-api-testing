#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用例读写与合并测试。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.importers.case_writer import merge_case_rows, read_cases, write_cases


class TestCaseWriter(unittest.TestCase):
    def test_write_and_read_csv_json(self):
        rows = [
            {"id": "1", "name": "a", "method": "GET", "url": "/api/test", "headers": "{}", "params": "{}", "body": "{}"},
            {"id": "2", "name": "b", "method": "POST", "url": "/api/login", "headers": "{}", "params": "{}", "body": "{}"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "cases.csv"
            json_path = Path(tmp) / "cases.json"
            write_cases(rows, csv_path, "csv")
            write_cases(rows, json_path, "json")
            self.assertEqual(len(read_cases(csv_path)), 2)
            self.assertEqual(len(read_cases(json_path)), 2)

    def test_merge_renumbers(self):
        original = [{"id": "1", "name": "o1", "method": "GET", "url": "/a"}]
        append = [{"id": "x", "name": "n1", "method": "POST", "url": "/b"}]
        merged = merge_case_rows(original, append)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["id"], "1")
        self.assertEqual(merged[1]["id"], "2")
        self.assertEqual(merged[1]["_source"], "appended")


if __name__ == "__main__":
    unittest.main()
