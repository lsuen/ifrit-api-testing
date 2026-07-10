#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""知识库入库：fixtures / api_docs / 外部需求文档。"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.importers.case_writer import CASE_COLUMNS, read_cases
from core.rag.chunker import chunk_text
from core.rag.paths import uploads_dir
from core.rag.store import RagStore

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".csv"}
CASE_SUFFIXES = {".csv", ".json"}


def _case_rows_to_text(rows: List[Dict[str, str]]) -> str:
    lines = []
    for row in rows[:200]:
        parts = [
            f"用例: {row.get('name', '')}",
            f"{row.get('method', 'GET')} {row.get('url', '')}",
            f"期望状态: {row.get('expected_status', '')}",
        ]
        if row.get("body"):
            parts.append(f"body: {row.get('body')}")
        if row.get("validate"):
            parts.append(f"validate: {row.get('validate')}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _read_text_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in CASE_SUFFIXES and (
        path.parent.name in {"csv", "json"} or "fixtures" in path.parts
    ):
        try:
            rows = read_cases(path)
            if rows and rows[0].get("method"):
                return _case_rows_to_text(rows)
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


class RagIngestor:
    def __init__(self, project_root: str):
        self.root = Path(project_root).resolve()
        self.store = RagStore(str(self.root))

    def ingest_text(
        self,
        text: str,
        source_type: str,
        source_path: str,
        title: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        chunks = chunk_text(text)
        if not chunks:
            return 0
        return self.store.upsert_document(source_type, source_path, title, chunks, meta)

    def ingest_file(self, file_path: Path, source_type: str = "requirement") -> int:
        file_path = file_path.resolve()
        if not file_path.is_file():
            raise FileNotFoundError(str(file_path))
        try:
            rel = str(file_path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            rel = str(file_path).replace("\\", "/")

        text = _read_text_file(file_path)
        title = file_path.name
        if source_type == "fixture":
            title = f"用例 {rel}"
        elif source_type == "api_doc":
            title = f"API文档 {rel}"
        elif source_type == "requirement":
            title = f"需求文档 {rel}"

        return self.ingest_text(
            text,
            source_type=source_type,
            source_path=rel,
            title=title,
            meta={"bytes": len(text.encode("utf-8"))},
        )

    def ingest_upload(
        self,
        filename: str,
        content: str,
        source_type: str = "requirement",
    ) -> Tuple[int, str]:
        safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in filename)
        upload_path = uploads_dir(str(self.root)) / safe_name
        upload_path.write_text(content, encoding="utf-8")
        rel = str(upload_path.relative_to(self.root)).replace("\\", "/")
        doc_id = self.ingest_text(
            content,
            source_type=source_type,
            source_path=rel,
            title=safe_name,
            meta={"upload": True},
        )
        return doc_id, rel

    def ingest_directory(
        self,
        directory: Path,
        source_type: str,
        patterns: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        if not directory.is_dir():
            return {"files": 0, "chunks": 0}
        files = 0
        chunks = 0
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if patterns and not any(path.match(p) for p in patterns):
                continue
            doc_id = self.ingest_file(path, source_type=source_type)
            if doc_id:
                files += 1
                with self.store._conn() as conn:
                    count = conn.execute(
                        "SELECT COUNT(*) AS c FROM chunks WHERE doc_id=?", (doc_id,)
                    ).fetchone()["c"]
                chunks += count
        return {"files": files, "chunks": chunks}

    def rebuild_all(self) -> Dict[str, Any]:
        summary = {"fixture": {}, "api_doc": {}, "upload": {}}
        fixtures = self.root / "fixtures"
        if fixtures.is_dir():
            summary["fixture"] = self.ingest_directory(fixtures, "fixture")
        api_docs = self.root / "api_docs"
        if api_docs.is_dir():
            summary["api_doc"] = self.ingest_directory(api_docs, "api_doc")
        uploads = uploads_dir(str(self.root))
        if uploads.is_dir():
            summary["upload"] = self.ingest_directory(uploads, "requirement")
        summary["stats"] = self.store.stats()
        return summary
