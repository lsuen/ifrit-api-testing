#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文档 URL 拉取与 Apifox 解析测试。"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agent.actions.fetch_document import FetchDocumentAction
from agent.parser.document_parser import DocumentParser
from agent.skills.registry import get_actions, list_skills


class TestDocInput(unittest.TestCase):
    def test_list_doc_url_skill(self):
        self.assertIn("doc_url_generation", list_skills())
        actions = get_actions("doc_url_generation")
        self.assertEqual(actions[0].name, "fetch_document")

    def test_parse_apifox_embedded_openapi(self):
        fixture = os.path.join(BASE_DIR, "tests", "fixtures", "apifox_address_add.md")
        apis = DocumentParser().parse_document(fixture, endpoints=["/api/address/add"])
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0]["method"], "POST")
        self.assertEqual(apis[0]["path"], "/api/address/add")
        self.assertTrue(apis[0]["auth_required"])

    def test_parse_address_group_from_swagger(self):
        spec = os.path.join(BASE_DIR, "api_docs", "apispec_1.json")
        apis = DocumentParser().parse_document(spec, endpoints=["/api/address"])
        paths = {item["path"] for item in apis}
        self.assertIn("/api/address/add", paths)
        self.assertIn("/api/address/list", paths)

    @patch("agent.utils.doc_fetch.requests.get")
    def test_fetch_document_action(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'{"openapi":"3.0.0","paths":{}}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = os.path.join(temp_dir, "cache")
            os.makedirs(cache_dir, exist_ok=True)
            with patch("agent.utils.doc_fetch.get_cache_dir", return_value=cache_dir):
                context = FetchDocumentAction().run(
                    {"input_url": "http://example.com/apispec.json"}
                )
                self.assertTrue(os.path.isfile(context["input_doc"]))


if __name__ == "__main__":
    unittest.main()
