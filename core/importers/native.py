#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""原生 CSV/JSON 用例导入（ifrit 格式）。"""
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.importers.case_writer import CASE_COLUMNS, read_cases


class NativeImportError(ValueError):
    """原生格式导入失败。"""


def import_native_file(import_file: Path) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    if not import_file.is_file():
        raise NativeImportError(f"文件不存在: {import_file}")

    suffix = import_file.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise NativeImportError(f"不支持的扩展名: {suffix}，请使用 .csv 或 .json")

    rows = read_cases(import_file)
    if not rows:
        raise NativeImportError("文件中没有用例行")

    missing = [col for col in ("name", "method", "url") if not any(row.get(col) for row in rows)]
    if missing:
        raise NativeImportError(f"用例缺少必要字段: {', '.join(missing)}")

    meta = {
        "collection_name": import_file.stem,
        "source": "native",
        "format": suffix.lstrip("."),
        "case_count": len(rows),
        "columns": CASE_COLUMNS,
    }
    return rows, meta
