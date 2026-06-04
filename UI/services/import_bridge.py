#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UI 侧导入桥接：调用 core 解析/保存（预览与落盘），诊断仍走 CLI subprocess。"""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _ensure_core_path(project_root: Path) -> None:
    root_str = str(project_root.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def preview_postman(project_root: Path, import_rel: str) -> Dict[str, Any]:
    _ensure_core_path(project_root)
    from core.importers.postman import PostmanImporter, PostmanImportError

    full_path = (project_root / import_rel.replace("\\", "/")).resolve()
    if not full_path.is_file():
        raise PostmanImportError(f"文件不存在: {import_rel}")
    rows, meta = PostmanImporter(str(full_path)).convert()
    return {"rows": rows, "meta": meta, "case_count": len(rows)}


def get_project_context(project_root: Path) -> Dict[str, Any]:
    _ensure_core_path(project_root)
    from core.project_context import build_project_context

    return build_project_context(project_root)


def save_merged_cases(
    project_root: Path,
    original_rows: List[Dict[str, Any]],
    append_rows: List[Dict[str, Any]],
    suite: str,
    output_format: str,
    output_rel: str = "",
    collection_name: str = "import",
) -> str:
    _ensure_core_path(project_root)
    from core.importers.case_writer import merge_case_rows, write_cases

    merged = merge_case_rows(original_rows, append_rows)
    if output_rel:
        out_path = (project_root / output_rel.replace("\\", "/")).resolve()
    else:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in collection_name)
        sub = "json" if output_format == "json" else "csv"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = project_root / "fixtures" / suite / sub / f"postman_{safe}_{stamp}.{sub}"
    write_cases(merged, out_path, output_format)
    return str(out_path.relative_to(project_root)).replace("\\", "/")


def write_save_payload(
    project_root: Path,
    original_rows: List[Dict[str, Any]],
    append_rows: List[Dict[str, Any]],
    suite: str,
    output_format: str,
    output_rel: str,
    collection_name: str,
) -> Path:
    payload = {
        "original_rows": original_rows,
        "append_rows": append_rows,
        "suite": suite,
        "output_format": output_format,
        "output": output_rel or None,
        "collection_name": collection_name,
    }
    temp_dir = project_root / "fixtures" / "import" / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".json", dir=str(temp_dir))
    import os

    os.close(fd)
    payload_path = Path(path)
    with open(payload_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return payload_path
