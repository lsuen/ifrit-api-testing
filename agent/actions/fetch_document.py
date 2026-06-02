#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：从 URL 拉取接口文档 Action，写入 context['input_doc']
"""
import logging
from typing import Any, Dict

from agent.actions.base import Action
from agent.utils.doc_fetch import fetch_document_to_cache

logger = logging.getLogger(__name__)


class FetchDocumentAction(Action):
    """拉取远程文档，将本地缓存路径写入 context['input_doc']。"""

    name = "fetch_document"
    description = "从 HTTP(S) URL 下载 Markdown / Swagger 文档到本地缓存"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        input_url = context.get("input_url")
        if not input_url:
            if context.get("input_doc"):
                return context
            raise ValueError("context 缺少 input_url")

        timeout = int(context.get("fetch_timeout", 30))
        local_path = fetch_document_to_cache(input_url, timeout=timeout)
        context["input_doc"] = local_path
        context["fetched_from_url"] = input_url
        logger.info("远程文档已就绪: %s", local_path)
        return context
