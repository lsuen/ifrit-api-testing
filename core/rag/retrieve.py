#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RAG 检索与 Prompt 格式化。"""
from typing import Any, Dict, List, Optional

from core.rag.store import RagStore

RAG_HIT_MARKER = "[IFRIT] RAG_HIT"


def format_hits(hits: List[Dict[str, Any]], max_chars: int = 6000) -> str:
    if not hits:
        return ""
    lines = ["## 项目知识库参考（RAG 检索）", "以下片段来自历史用例、API 文档或需求文档，生成时请对齐风格与字段约定：", ""]
    used = 0
    for index, hit in enumerate(hits, start=1):
        block = (
            f"### 片段 {index} [{hit.get('source_type')}] {hit.get('title')}\n"
            f"来源: {hit.get('source_path')}\n"
            f"{hit.get('content', '').strip()}\n"
        )
        if used + len(block) > max_chars:
            break
        lines.append(block)
        used += len(block)
    return "\n".join(lines).strip()


class RagService:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.store = RagStore(project_root)

    def stats(self) -> Dict[str, Any]:
        return self.store.stats()

    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.store.list_documents(limit)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        return self.store.search(query, top_k=top_k, source_types=source_types)

    def retrieve_for_prompt(
        self,
        query: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
        emit_log: bool = True,
    ) -> str:
        hits = self.search(query, top_k=top_k, source_types=source_types)
        if emit_log:
            sources = sorted({h.get("source_type", "") for h in hits})
            print(
                f"{RAG_HIT_MARKER} n={len(hits)} top_k={top_k} "
                f"sources={','.join(sources) or 'none'} query={query[:80]}",
                flush=True,
            )
        return format_hits(hits)

    @staticmethod
    def build_query(
        *,
        endpoints: Optional[List[str]] = None,
        input_doc: Optional[str] = None,
        input_url: Optional[str] = None,
        user_hint: Optional[str] = None,
        case_names: Optional[List[str]] = None,
    ) -> str:
        parts: List[str] = []
        if endpoints:
            parts.extend(endpoints)
        if input_doc:
            parts.append(input_doc)
        if input_url:
            parts.append(input_url)
        if user_hint:
            parts.append(user_hint)
        if case_names:
            parts.extend(case_names[:10])
        return " ".join(p for p in parts if p).strip() or "API 测试用例"
