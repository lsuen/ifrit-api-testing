#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文件树与在线编辑（高级模式）。"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SUPPORTED_EXTENSIONS = {
    ".txt", ".csv", ".json", ".yaml", ".yml", ".ini", ".cfg",
    ".py", ".js", ".html", ".css", ".md", ".xml", ".sh", ".bat",
    ".log", ".conf", ".properties", ".env", ".toml",
}

ACE_MODE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".json": "json",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".ini": "ini",
    ".sh": "sh",
    ".bat": "batchfile",
    ".csv": "csv",
    ".log": "text",
    ".txt": "text",
}


def build_file_tree(directory_path: Path) -> List[Dict[str, Any]]:
    if not directory_path.is_dir():
        return []

    tree = []
    try:
        items = sorted(directory_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    except PermissionError:
        return []

    for item in items:
        if item.name.startswith(".") or item.name == "__pycache__":
            continue
        node: Dict[str, Any] = {
            "name": item.name,
            "path": str(item),
            "is_dir": item.is_dir(),
        }
        if item.is_dir():
            node["children"] = build_file_tree(item)
        else:
            stat = item.stat()
            node["size"] = stat.st_size
            node["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            node["extension"] = item.suffix.lower()
            node["supported"] = item.suffix.lower() in SUPPORTED_EXTENSIONS
        tree.append(node)
    return tree


def read_file_content(file_path: Path) -> Tuple[bool, str, Optional[str]]:
    if not file_path.is_file():
        return False, "文件不存在", None
    if file_path.stat().st_size > 10 * 1024 * 1024:
        return False, "文件过大（>10MB）", None
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, f"不支持编辑 {file_path.suffix}", None

    for encoding in ("utf-8", "gbk"):
        try:
            with open(file_path, "r", encoding=encoding) as handle:
                return True, handle.read(), encoding
        except UnicodeDecodeError:
            continue
        except OSError as error:
            return False, str(error), None
    return False, "无法解码文件", None


def save_file_content(file_path: Path, content: str, encoding: str = "utf-8") -> Tuple[bool, str]:
    if not file_path.is_file():
        return False, "文件不存在"
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, "不支持该格式"
    try:
        with open(file_path, "w", encoding=encoding) as handle:
            handle.write(content)
        return True, "保存成功"
    except OSError as error:
        return False, str(error)
