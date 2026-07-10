#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SQLite + FTS5 知识库存储。"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from core.rag.paths import db_path, rag_root


class RagStore:
    def __init__(self, project_root: str):
        self.project_root = str(Path(project_root).resolve())
        self.db_file = db_path(self.project_root)
        rag_root(self.project_root).mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    meta_json TEXT DEFAULT '{}',
                    ingested_at TEXT NOT NULL,
                    UNIQUE(source_type, source_path)
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    meta_json TEXT DEFAULT '{}',
                    FOREIGN KEY(doc_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    content,
                    title,
                    source_type,
                    source_path,
                    tokenize='unicode61'
                );
                """
            )

    def stats(self) -> Dict[str, Any]:
        with self._conn() as conn:
            docs = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
            chunks = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()["c"]
            by_type = conn.execute(
                "SELECT source_type, COUNT(*) AS c FROM documents GROUP BY source_type"
            ).fetchall()
        try:
            db_display = str(Path(self.db_file).relative_to(Path(self.project_root))).replace("\\", "/")
        except ValueError:
            db_display = str(self.db_file)
        return {
            "db_path": db_display,
            "documents": docs,
            "chunks": chunks,
            "by_source_type": {row["source_type"]: row["c"] for row in by_type},
        }

    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT d.*, (
                    SELECT COUNT(*) FROM chunks c WHERE c.doc_id = d.id
                ) AS chunk_count
                FROM documents d
                ORDER BY d.ingested_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_document(self, doc_id: int) -> None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM chunks WHERE doc_id=?", (doc_id,)
            ).fetchall()
            for item in row:
                conn.execute(
                    "DELETE FROM chunks_fts WHERE rowid=?", (item["id"],)
                )
            conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))

    def upsert_document(
        self,
        source_type: str,
        source_path: str,
        title: str,
        chunks: List[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        if not chunks:
            return 0
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM documents WHERE source_type=? AND source_path=?",
                (source_type, source_path),
            ).fetchone()
            if existing:
                doc_id = existing["id"]
                old_chunks = conn.execute(
                    "SELECT id FROM chunks WHERE doc_id=?", (doc_id,)
                ).fetchall()
                for item in old_chunks:
                    conn.execute("DELETE FROM chunks_fts WHERE rowid=?", (item["id"],))
                conn.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
                conn.execute(
                    """
                    UPDATE documents
                    SET title=?, meta_json=?, ingested_at=?
                    WHERE id=?
                    """,
                    (title, meta_json, now, doc_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO documents(source_type, source_path, title, meta_json, ingested_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (source_type, source_path, title, meta_json, now),
                )
                doc_id = cur.lastrowid

            for index, content in enumerate(chunks):
                cur = conn.execute(
                    """
                    INSERT INTO chunks(doc_id, chunk_index, content, meta_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_id, index, content, meta_json),
                )
                chunk_id = cur.lastrowid
                conn.execute(
                    """
                    INSERT INTO chunks_fts(rowid, content, title, source_type, source_path)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chunk_id, content, title, source_type, source_path),
                )
        return doc_id

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        terms = [t for t in query.replace("/", " ").split() if len(t) >= 2]
        if not terms:
            terms = [query]
        fts_query = " OR ".join(f'"{term}"' for term in terms[:12])

        sql = """
            SELECT
                c.id AS chunk_id,
                c.content,
                c.chunk_index,
                d.id AS doc_id,
                d.title,
                d.source_type,
                d.source_path,
                bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            JOIN documents d ON d.id = c.doc_id
            WHERE chunks_fts MATCH ?
        """
        params: List[Any] = [fts_query]
        if source_types:
            placeholders = ",".join("?" for _ in source_types)
            sql += f" AND d.source_type IN ({placeholders})"
            params.extend(source_types)
        sql += " ORDER BY score LIMIT ?"
        params.append(top_k)

        with self._conn() as conn:
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                return []

        hits = []
        for row in rows:
            hits.append(
                {
                    "chunk_id": row["chunk_id"],
                    "content": row["content"],
                    "chunk_index": row["chunk_index"],
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "source_type": row["source_type"],
                    "source_path": row["source_path"],
                    "score": row["score"],
                }
            )
        return hits
