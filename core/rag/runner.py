#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RAG CLI 入口。"""
import json
import sys
from argparse import Namespace
from pathlib import Path


def run_rag_command(args: Namespace) -> int:
    project_root = getattr(args, "project_root", ".") or "."
    from core.rag.service import KnowledgeService

    service = KnowledgeService(project_root)

    if getattr(args, "rag_stats", False):
        print("[IFRIT] RAG_STATS " + json.dumps(service.stats(), ensure_ascii=False))
        return 0

    if getattr(args, "rag_rebuild", False):
        print("[IFRIT] RAG rebuild start")
        summary = service.rebuild_all()
        print("[IFRIT] RAG rebuild done " + json.dumps(summary, ensure_ascii=False))
        return 0

    ingest_path = getattr(args, "rag_ingest", None)
    if ingest_path:
        path = Path(ingest_path)
        if not path.is_file():
            print(f"[IFRIT] RAG ingest 文件不存在: {path}")
            return 1
        source_type = getattr(args, "rag_source_type", "requirement") or "requirement"
        doc_id = service.ingest_file(str(path), source_type=source_type)
        print(f"[IFRIT] RAG ingest ok doc_id={doc_id} path={ingest_path}")
        return 0

    query = getattr(args, "rag_query", None)
    if query:
        top_k = getattr(args, "rag_top_k", 5) or 5
        text = service.retrieve_for_prompt(query, top_k=top_k)
        print(text or "[IFRIT] RAG 无命中")
        return 0

    print("[IFRIT] 请指定 --rag-stats / --rag-rebuild / --rag-ingest / --rag-query")
    return 1
