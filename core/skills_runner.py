#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 商店 CLI 入口（刷新 / 列表，stdout 流式 [IFRIT] 标记）。"""
import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Optional

from agent.skills.catalog import build_catalog, install_skill, uninstall_skill, set_skill_enabled
from agent.skills.paths import SkillStorePaths
from agent.skills.registry import list_skills_detail
from agent.skills.repos import add_repo, load_repos, refresh_all, remove_repo

CATALOG_MARKER = "[IFRIT] SKILL_CATALOG_JSON="


def run_skills_list(args: Namespace) -> int:
    root = Path(getattr(args, "project_root", ".") or ".").resolve()
    paths = SkillStorePaths(str(root))
    builtin = list_skills_detail()
    query = getattr(args, "skills_query", None) or getattr(args, "query", "") or ""
    catalog = [item.to_dict() for item in build_catalog(paths, query=query)]
    payload = {"builtin": builtin, "catalog": catalog}
    print(CATALOG_MARKER + json.dumps(payload, ensure_ascii=False))
    print(f"[IFRIT] skills builtin={len(builtin)} catalog={len(catalog)}")
    return 0


def run_skills_refresh(args: Namespace) -> int:
    root = Path(getattr(args, "project_root", ".") or ".").resolve()
    paths = SkillStorePaths(str(root))

    def log(msg: str) -> None:
        print(msg, flush=True)

    repo_id = getattr(args, "skills_repo_id", None)
    if repo_id:
        from agent.skills.repos import refresh_repo

        repos = load_repos(paths)
        repo = next((r for r in repos if r.id == repo_id), None)
        if not repo:
            print(f"[IFRIT] 仓库不存在: {repo_id}")
            return 1
        ok, err = refresh_repo(paths, repo, log=log)
        from agent.skills.repos import save_repos

        save_repos(paths, repos)
        return 0 if ok else 1

    result = refresh_all(paths, log=log)
    print(
        f"[IFRIT] SKILL_REFRESH done ok={result['ok']} failed={result['failed']}",
        flush=True,
    )
    return 0 if result["failed"] == 0 else 1


def run_skills_install(args: Namespace) -> int:
    root = Path(getattr(args, "project_root", ".") or ".").resolve()
    paths = SkillStorePaths(str(root))
    skill_id = args.skills_install
    try:
        dest = install_skill(paths, skill_id)
        print(f"[IFRIT] SKILL_INSTALL ok id={skill_id} path={dest.as_posix()}")
        return 0
    except Exception as error:
        print(f"[IFRIT] SKILL_INSTALL failed id={skill_id} error={error}")
        return 1


def run_skills_command(args: Namespace) -> int:
    if getattr(args, "skills_list", False):
        return run_skills_list(args)
    if getattr(args, "skills_refresh", False):
        return run_skills_refresh(args)
    if getattr(args, "skills_install", None):
        return run_skills_install(args)
    print("[IFRIT] 未指定 skills 子命令")
    return 1
