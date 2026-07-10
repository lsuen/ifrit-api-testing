#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""UI Skill 管理桥接。"""
import sys
from pathlib import Path
from typing import Any, Dict, List

UI_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = UI_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.skills.catalog import (  # noqa: E402
    build_catalog,
    install_skill,
    read_skill_content,
    save_skill_content,
    set_skill_enabled,
    uninstall_skill,
)
from agent.skills.paths import SkillStorePaths  # noqa: E402
from agent.skills.registry import list_action_names, list_skills_detail  # noqa: E402
from agent.skills.repos import add_repo, load_repos, remove_repo  # noqa: E402


def _paths(root: Path) -> SkillStorePaths:
    return SkillStorePaths(str(root))


def get_builtin_skills() -> List[Dict[str, Any]]:
    return list_skills_detail()


def get_catalog(root: Path, query: str = "") -> List[Dict[str, Any]]:
    return [item.to_dict() for item in build_catalog(_paths(root), query=query)]


def get_repos(root: Path) -> List[Dict[str, Any]]:
    paths = _paths(root)
    repos = load_repos(paths)
    catalog = build_catalog(paths)
    counts: Dict[str, int] = {}
    for item in catalog:
        counts[item.repo_id] = counts.get(item.repo_id, 0) + 1
    return [
        {
            "id": r.id,
            "host": r.host,
            "owner": r.owner,
            "repo": r.repo,
            "branch": r.branch,
            "enabled": r.enabled,
            "label": r.label(),
            "clone_url": r.clone_url(),
            "last_refresh_at": r.last_refresh_at,
            "last_error": r.last_error,
            "skill_count": counts.get(r.id, 0),
            "cached": paths.repo_cache_dir(r.id).is_dir(),
        }
        for r in repos
    ]


def add_repo_url(root: Path, url: str, branch: str = "main") -> Dict[str, Any]:
    repo = add_repo(_paths(root), url, branch)
    return {
        "id": repo.id,
        "label": repo.label(),
        "clone_url": repo.clone_url(),
    }


def remove_repo_by_id(root: Path, repo_id: str) -> bool:
    return remove_repo(_paths(root), repo_id)


def install(root: Path, skill_id: str) -> str:
    dest = install_skill(_paths(root), skill_id)
    return str(dest)


def uninstall(root: Path, skill_id: str) -> None:
    uninstall_skill(_paths(root), skill_id)


def enable(root: Path, skill_id: str, enabled: bool) -> None:
    set_skill_enabled(_paths(root), skill_id, enabled)


def read_editor(root: Path, skill_id: str) -> Dict[str, Any]:
    return read_skill_content(_paths(root), skill_id)


def save_editor(root: Path, skill_id: str, content: str) -> None:
    save_skill_content(_paths(root), skill_id, content)


def get_actions_catalog() -> List[str]:
    return list_action_names()
