#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：解析接口文档 Action，从 context 读取文档路径并提取 API 列表
创建时间：2026-06-02
"""

import logging
from typing import Any, Dict

from agent.actions.base import Action
from agent.parser.document_parser import DocumentParser

logger = logging.getLogger(__name__)


class ParseDocumentAction(Action):
    """解析输入文档，将 API 列表写入 context['apis']。"""

    name = "parse_document"
    description = "解析 Markdown / Swagger 接口文档，提取 API 信息"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        doc_path = context.get("input_doc")
        if not doc_path:
            raise ValueError("context 缺少 input_doc")

        endpoints = context.get("endpoints")
        parser = context.get("parser") or DocumentParser()
        apis = parser.parse_document(doc_path, endpoints)

        if not apis:
            raise ValueError(f"未能从文档解析出 API: {doc_path}")

        context["apis"] = apis
        context["parser"] = parser
        logger.info("解析文档完成，共 %d 个 API", len(apis))
        return context
