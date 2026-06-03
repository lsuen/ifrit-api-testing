#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ifrit 项目路径与统计。"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.config_loader import project_path


def list_test_files(root: Path, extensions: Optional[List[str]] = None, project_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    if not root.exists():
        return []
    extensions = extensions or [".csv", ".xlsx", ".xls", ".json"]
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        if "__pycache__" in path.parts:
            continue
        stat = path.stat()
        rel = path.name
        if project_root:
            try:
                rel = str(path.relative_to(project_root)).replace("\\", "/")
            except ValueError:
                rel = str(path)
        files.append(
            {
                "name": path.name,
                "path": str(path),
                "relative": rel,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return files


def list_api_docs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    docs_dir = project_path(config, "api_docs")
    root = config["ifrit"]["root_path_resolved"]
    return list_test_files(docs_dir, [".json", ".yaml", ".yml", ".md", ".markdown"], project_root=root)


def list_report_runs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    runs_dir = project_path(config, "reports_runs")
    if not runs_dir.is_dir():
        return []

    runs = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        meta = {}
        meta_path = run_dir / "meta.json"
        if meta_path.is_file():
            try:
                with open(meta_path, "r", encoding="utf-8") as handle:
                    meta = json.load(handle)
            except (json.JSONDecodeError, OSError):
                meta = {}

        html_index = run_dir / "html" / "index.html"
        allure_dir = run_dir / "allure-results"
        stat = run_dir.stat()
        runs.append(
            {
                "run_id": run_dir.name,
                "path": str(run_dir),
                "created_at": meta.get("created_at") or datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "suite": meta.get("suite", ""),
                "has_html": html_index.is_file(),
                "html_url": f"/reports/view/{run_dir.name}",
                "allure_count": len(list(allure_dir.glob("*"))) if allure_dir.is_dir() else 0,
            }
        )
    return runs


def get_latest_run_id(config: Dict[str, Any]) -> Optional[str]:
    latest_file = project_path(config, "reports_latest")
    if not latest_file.is_file():
        return None
    return latest_file.read_text(encoding="utf-8").strip() or None


def count_cases_in_dir(directory: Path) -> Optional[int]:
    """统计目录下 CSV 用例行数；目录不存在返回 None。"""
    if not directory.is_dir():
        return None
    total = 0
    for csv_path in directory.rglob("*.csv"):
        try:
            with open(csv_path, "r", encoding="utf-8") as handle:
                lines = [line for line in handle.readlines() if line.strip() and not line.startswith("#")]
            total += max(0, len(lines) - 1)
        except OSError:
            continue
    return total


def dashboard_stats(config: Dict[str, Any]) -> Dict[str, Any]:
    root = config["ifrit"]["root_path_resolved"]
    fixtures = root / "fixtures"
    runs_dir = project_path(config, "reports_runs")
    manual = count_cases_in_dir(fixtures / "manual" / "csv")
    ai = count_cases_in_dir(fixtures / "ai" / "csv")
    smoke = count_cases_in_dir(fixtures / "smoke" / "csv")
    runs = list_report_runs(config) if runs_dir.is_dir() else []
    latest = get_latest_run_id(config)
    return {
        "manual_cases": manual,
        "ai_cases": ai,
        "smoke_cases": smoke,
        "report_runs": len(runs) if runs_dir.is_dir() else None,
        "latest_run": latest,
        "latest_runs": runs[:5],
    }
