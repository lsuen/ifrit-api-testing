#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RAG 对外服务门面。"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.rag.ingest import RagIngestor
from core.rag.retrieve import RagService, format_hits


class KnowledgeService(RagService):
    """RAG 服务：检索 + 入库。"""

    def __init__(self, project_root: str):
        super().__init__(project_root)
        self.ingestor = RagIngestor(project_root)

    def ingest_file(self, file_path: str, source_type: str = "requirement") -> int:
        return self.ingestor.ingest_file(Path(file_path), source_type=source_type)

    def ingest_upload(
        self,
        filename: str,
        content: str,
        source_type: str = "requirement",
    ) -> Tuple[int, str]:
        return self.ingestor.ingest_upload(filename, content, source_type=source_type)

    def rebuild_all(self) -> Dict[str, Any]:
        return self.ingestor.rebuild_all()

    def delete_document(self, doc_id: int) -> None:
        self.store.delete_document(doc_id)


__all__ = ["KnowledgeService", "RagService", "format_hits"]
