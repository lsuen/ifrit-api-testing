#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RAG 知识库单元测试。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.rag.service import KnowledgeService


class TestRag(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        Path(self.root, "api_docs").mkdir()
        Path(self.root, "api_docs", "sample.md").write_text(
            "# 地址接口\nPOST /api/address/add 需要鉴权 token\n边界值测试 phone 11 位",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_ingest_and_search(self):
        service = KnowledgeService(self.root)
        doc_id, rel = service.ingest_upload("req.md", "用户必须先登录再添加地址", "requirement")
        self.assertGreater(doc_id, 0)
        service.rebuild_all()
        hits = service.search("address 鉴权", top_k=3)
        self.assertTrue(hits)
        formatted = service.retrieve_for_prompt("address add", top_k=2, emit_log=False)
        self.assertIn("知识库", formatted)

    def test_stats(self):
        service = KnowledgeService(self.root)
        service.ingest_upload("a.txt", "hello rag", "requirement")
        stats = service.stats()
        self.assertGreaterEqual(stats["documents"], 1)
        self.assertGreaterEqual(stats["chunks"], 1)


if __name__ == "__main__":
    unittest.main()
