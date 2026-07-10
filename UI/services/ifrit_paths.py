#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ifrit 项目路径与统计。"""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.config_loader import project_path

RUN_ID_PATTERN = re.compile(r"^[\w-]+$")


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
                "relative_path": f"reports/runs/{run_dir.name}",
                "created_at": meta.get("created_at") or datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "suite": meta.get("suite", ""),
                "has_html": html_index.is_file(),
                "has_allure": allure_dir.is_dir() and any(allure_dir.iterdir()) if allure_dir.is_dir() else False,
                "html_url": f"/reports/view/{run_dir.name}/",
                "allure_count": len(list(allure_dir.glob("*"))) if allure_dir.is_dir() else 0,
            }
        )
    return runs


def resolve_report_html_file(config: Dict[str, Any], run_id: str, subpath: Optional[str] = None) -> Optional[Path]:
    """安全解析 run 下 html 目录内的文件（防路径穿越）。"""
    if not RUN_ID_PATTERN.match(run_id or ""):
        return None
    html_dir = project_path(config, "reports_runs") / run_id / "html"
    if not html_dir.is_dir():
        return None
    html_resolved = html_dir.resolve()
    if subpath:
        target = (html_dir / subpath).resolve()
        try:
            target.relative_to(html_resolved)
        except ValueError:
            return None
        return target if target.is_file() else None
    index_path = html_dir / "index.html"
    return index_path if index_path.is_file() else None


def delete_report_run(config: Dict[str, Any], run_id: str) -> bool:
    if not RUN_ID_PATTERN.match(run_id or ""):
        return False
    runs_dir = project_path(config, "reports_runs")
    run_dir = runs_dir / run_id
    if not run_dir.is_dir():
        return False
    shutil.rmtree(run_dir)
    latest_file = project_path(config, "reports_latest")
    if latest_file.is_file() and latest_file.read_text(encoding="utf-8").strip() == run_id:
        remaining = list_report_runs(config)
        if remaining:
            latest_file.write_text(remaining[0]["run_id"], encoding="utf-8")
        else:
            latest_file.unlink(missing_ok=True)
    return True


def generate_run_html_report(config: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    if not RUN_ID_PATTERN.match(run_id or ""):
        return {"ok": False, "error": "无效的 run_id"}
    run_dir = project_path(config, "reports_runs") / run_id
    allure_dir = run_dir / "allure-results"
    html_dir = run_dir / "html"
    if not allure_dir.is_dir() or not any(allure_dir.iterdir()):
        return {"ok": False, "error": "该 Run 无 Allure 结果，请先执行测试"}
    root = config["ifrit"]["root_path_resolved"]
    if str(root) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(root))
    from core.report_manager import ReportManager

    ok = ReportManager().generate_html_report(str(allure_dir), str(html_dir))
    if not ok:
        return {"ok": False, "error": "HTML 生成失败，请确认已安装 allure 命令行"}
    return {"ok": True, "html_url": f"/reports/view/{run_id}/"}


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
