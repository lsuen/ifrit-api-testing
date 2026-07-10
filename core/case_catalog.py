#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fixtures 用例目录浏览。"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.importers.case_writer import read_cases


def list_case_files(project_root: Path, suite: Optional[str] = None) -> List[Dict[str, Any]]:
    root = project_root.resolve()
    fixtures = root / "fixtures"
    if not fixtures.is_dir():
        return []

    items: List[Dict[str, Any]] = []
    suites = [suite] if suite else ["smoke", "manual", "ai"]
    for suite_name in suites:
        for sub in ("csv", "json"):
            directory = fixtures / suite_name / sub
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob(f"*.{sub}")):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(root)).replace("\\", "/")
                count = None
                try:
                    count = len(read_cases(path))
                except (OSError, ValueError):
                    pass
                items.append(
                    {
                        "relative": rel,
                        "suite": suite_name,
                        "format": sub,
                        "name": path.name,
                        "case_count": count,
                    }
                )
    return items
