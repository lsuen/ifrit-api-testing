#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""项目文档与 About 页数据（只读，渲染仓库内已有 md/yaml）。"""
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from services.config_loader import load_auth_summary, load_environment_options
from services.ifrit_paths import dashboard_stats

# 允许 UI 读取的文档（相对项目根）
DOC_FILES: Dict[str, str] = {
    "manual": "用户详细使用手册.md",
    "cli": "__docs/ifrit命令手册.md",
}

RECIPES_FILE = "__docs/cli_recipes.yaml"
README_FILE = "README.md"


def _read_text(root: Path, rel: str) -> Optional[str]:
    path = (root / rel.replace("/", "\\")).resolve()
    root_resolved = root.resolve()
    if not str(path).startswith(str(root_resolved)):
        return None
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def get_git_version(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ""


def load_cli_recipes(root: Path) -> List[Dict[str, Any]]:
    text = _read_text(root, RECIPES_FILE)
    if not text:
        return []
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return []
    groups = data.get("groups") or []
    if not isinstance(groups, list):
        return []
    return groups


def get_project_info(config: Dict[str, Any]) -> Dict[str, Any]:
    root: Path = config["ifrit"]["root_path_resolved"]
    stats = dashboard_stats(config)
    envs = load_environment_options(config)
    auth = load_auth_summary(config)
    readme = _read_text(root, README_FILE) or ""
    tagline = ""
    for line in readme.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">"):
            tagline = stripped
            break
        if stripped.startswith(">") and "面向" not in stripped:
            tagline = stripped.lstrip(">").strip()
            if tagline:
                break

    version = get_git_version(root) or "获取不到"
    return {
        "name": "ifrit API 自动化测试平台",
        "version": version,
        "tagline": tagline or "API 自动化 · AI 用例 · 报告",
        "project_root": str(root),
        "python_bin": config["ifrit"].get("python_bin", "python"),
        "ui_version": "2.0",
        "stats": stats,
        "environments": envs,
        "auth": {
            "available": auth.get("available"),
            "login_path": auth.get("login_path"),
            "username": auth.get("username"),
            "enabled": auth.get("enabled"),
        },
        "doc_sources": {
            "manual": DOC_FILES["manual"],
            "cli_manual": DOC_FILES["cli"],
            "cli_recipes": RECIPES_FILE,
        },
    }


def get_manual_markdown(config: Dict[str, Any]) -> Dict[str, Any]:
    root: Path = config["ifrit"]["root_path_resolved"]
    content = _read_text(root, DOC_FILES["manual"])
    if content is None:
        return {"success": False, "error": "用户手册不存在", "source": DOC_FILES["manual"]}
    return {"success": True, "source": DOC_FILES["manual"], "content": content}


def get_cli_docs(config: Dict[str, Any]) -> Dict[str, Any]:
    root: Path = config["ifrit"]["root_path_resolved"]
    manual = _read_text(root, DOC_FILES["cli"])
    recipes = load_cli_recipes(root)
    if manual is None and not recipes:
        return {"success": False, "error": "CLI 文档不存在"}
    return {
        "success": True,
        "manual_source": DOC_FILES["cli"],
        "manual_content": manual or "",
        "recipes": recipes,
        "help_hint": "python main.py --help",
    }
