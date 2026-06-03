#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导入 CLI 入口。"""
import json
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from core.importers.postman import PostmanImporter, PostmanImportError

SUPPORTED_FORMATS = {"postman"}


def _default_output_path(import_file: Path, suite: str, collection_name: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in collection_name)
    return Path("fixtures") / suite / "csv" / f"postman_{safe_name}_{stamp}.csv"


def run_import(args: Namespace) -> int:
    import_file = Path(args.import_file)
    import_format = (args.import_format or "postman").lower()
    suite = args.import_suite or "manual"
    dry_run = bool(getattr(args, "import_dry_run", False))
    ai_enhance = bool(getattr(args, "import_ai_enhance", False))

    if import_format not in SUPPORTED_FORMATS:
        print(f"[IFRIT] 不支持的导入格式: {import_format}")
        return 1

    try:
        if import_format == "postman":
            importer = PostmanImporter(str(import_file))
            rows, meta = importer.convert()
    except PostmanImportError as error:
        print(f"[IFRIT] 导入失败: {error}")
        return 1

    output_path = Path(args.import_output) if args.import_output else _default_output_path(
        import_file, suite, meta["collection_name"]
    )
    output_path = output_path.as_posix() if isinstance(output_path, Path) else str(output_path)
    output = Path(output_path)

    summary: Dict[str, Any] = {
        **meta,
        "suite": suite,
        "output": str(output).replace("\\", "/"),
        "dry_run": dry_run,
        "ai_enhance": ai_enhance,
    }

    if dry_run:
        print("[IFRIT] 导入预览 (dry-run)")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"[IFRIT] 用例预览(前3条): {json.dumps(rows[:3], ensure_ascii=False)}")
        return 0

    PostmanImporter.write_csv(rows, output)
    print(
        f"[IFRIT] 导入完成 format={import_format} 条数={len(rows)} "
        f"输出={output.as_posix()} suite={suite}"
    )

    if ai_enhance:
        print("[IFRIT] 提示: AI 增强将在后续版本支持，当前已完成 Postman 纯转换")

    return 0
