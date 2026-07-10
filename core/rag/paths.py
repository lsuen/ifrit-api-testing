#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RAG 存储路径约定。"""
from pathlib import Path


def rag_root(project_root: str) -> Path:
    return Path(project_root).resolve() / ".ifrit" / "rag"


def db_path(project_root: str) -> Path:
    return rag_root(project_root) / "knowledge.db"


def uploads_dir(project_root: str) -> Path:
    path = rag_root(project_root) / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path
