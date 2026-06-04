#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导入 CLI 入口。"""
import json
import sys
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.importers.case_writer import merge_case_rows, read_cases, write_cases
from core.importers.diagnose import ImportDiagnosisError, ImportDiagnosisService
from core.importers.postman import PostmanImporter, PostmanImportError
from core.project_context import format_project_context_for_prompt

SUPPORTED_FORMATS = {"postman"}
PREVIEW_MARKER = "[IFRIT] IMPORT_PREVIEW_JSON="
DIAGNOSE_MARKER = "[IFRIT] IMPORT_DIAGNOSE_JSON="


def _default_output_path(import_file: Path, suite: str, collection_name: str, output_format: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in collection_name)
    ext = "json" if output_format == "json" else "csv"
    sub = "json" if output_format == "json" else "csv"
    return Path("fixtures") / suite / sub / f"postman_{safe_name}_{stamp}.{ext}"


def _parse_postman(import_file: Path) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    importer = PostmanImporter(str(import_file))
    return importer.convert()


def run_preview(args: Namespace) -> int:
    import_file = Path(args.import_file)
    try:
        rows, meta = _parse_postman(import_file)
    except PostmanImportError as error:
        print(f"[IFRIT] 导入失败: {error}")
        return 1
    payload = {"rows": rows, "meta": meta, "case_count": len(rows)}
    print(PREVIEW_MARKER + json.dumps(payload, ensure_ascii=False))
    print(f"[IFRIT] 预览完成 条数={len(rows)} collection={meta.get('collection_name', '')}")
    return 0


def run_diagnose(args: Namespace) -> int:
    import_file = Path(args.import_file)
    inject = bool(getattr(args, "inject_project_context", False))
    try:
        rows, meta = _parse_postman(import_file)
    except PostmanImportError as error:
        print(f"[IFRIT] 导入失败: {error}")
        return 1

    project_context = None
    if inject:
        project_root = Path(getattr(args, "project_root", ".") or ".").resolve()
        project_context = format_project_context_for_prompt(project_root)

    try:
        service = ImportDiagnosisService()
        result = service.diagnose(rows, meta=meta, project_context=project_context)
    except ImportDiagnosisError as error:
        print(f"[IFRIT] 诊断失败: {error}")
        return 1

    result["meta"] = meta
    result["original_count"] = len(rows)
    print(DIAGNOSE_MARKER + json.dumps(result, ensure_ascii=False))
    print(
        f"[IFRIT] 诊断完成 原用例={len(rows)} "
        f"建议追加={len(result.get('suggested_cases', []))} "
        f"诊断项={len(result.get('diagnosis', []))}"
    )
    return 0


def run_save_payload(args: Namespace) -> int:
    payload_path = Path(args.import_payload)
    if not payload_path.is_file():
        print(f"[IFRIT] payload 文件不存在: {payload_path}")
        return 1
    with open(payload_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    original = payload.get("original_rows") or []
    append = payload.get("append_rows") or []
    output_format = payload.get("output_format", "csv")
    suite = payload.get("suite", "manual")
    output = payload.get("output")

    merged = merge_case_rows(original, append)
    if output:
        out_path = Path(output)
    else:
        name = payload.get("collection_name", "import")
        out_path = _default_output_path(payload_path, suite, name, output_format)

    write_cases(merged, out_path, output_format)
    print(
        f"[IFRIT] 保存完成 format={output_format} 原={len(original)} "
        f"追加={len(append)} 合计={len(merged)} 输出={out_path.as_posix()}"
    )
    return 0


def run_import(args: Namespace) -> int:
    if getattr(args, "import_preview_only", False):
        return run_preview(args)
    if getattr(args, "import_diagnose", False):
        return run_diagnose(args)
    if getattr(args, "import_payload", None):
        return run_save_payload(args)

    import_file = Path(args.import_file)
    import_format = (args.import_format or "postman").lower()
    suite = args.import_suite or "manual"
    dry_run = bool(getattr(args, "import_dry_run", False))
    output_format = getattr(args, "import_output_format", "csv") or "csv"

    if import_format not in SUPPORTED_FORMATS:
        print(f"[IFRIT] 不支持的导入格式: {import_format}")
        return 1

    try:
        if import_format == "postman":
            rows, meta = _parse_postman(import_file)
    except PostmanImportError as error:
        print(f"[IFRIT] 导入失败: {error}")
        return 1

    output_path = Path(args.import_output) if args.import_output else _default_output_path(
        import_file, suite, meta["collection_name"], output_format
    )
    output = Path(output_path)

    if dry_run:
        payload = {
            "rows": rows,
            "meta": meta,
            "suite": suite,
            "output_format": output_format,
            "output": str(output).replace("\\", "/"),
            "dry_run": True,
        }
        print("[IFRIT] 导入预览 (dry-run)")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"[IFRIT] 用例预览(前3条): {json.dumps(rows[:3], ensure_ascii=False)}")
        return 0

    write_cases(rows, output, output_format)
    print(
        f"[IFRIT] 导入完成 format={import_format} 条数={len(rows)} "
        f"输出={output.as_posix()} suite={suite} 格式={output_format}"
    )
    return 0
