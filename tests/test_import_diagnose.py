#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导入诊断测试（Mock LLM）。"""
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.importers.diagnose import ImportDiagnosisService


class TestImportDiagnose(unittest.TestCase):
    def test_parse_response_json(self):
        text = """```json
{"diagnosis":[{"category":"missing_boundary","endpoint":"/api/x","detail":"缺边界"}],
"suggested_cases":[],"summary":"ok"}
```"""
        data = ImportDiagnosisService._parse_response(text)
        self.assertEqual(len(data["diagnosis"]), 1)
        self.assertEqual(data["summary"], "ok")


if __name__ == "__main__":
    unittest.main()
