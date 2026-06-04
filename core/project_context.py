#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""构建导入/诊断时注入 LLM 的项目上下文摘要。"""
import configparser
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _count_csv_cases(directory: Path) -> Optional[int]:
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


def build_project_context(project_root: Path) -> Dict[str, Any]:
    """从真实配置文件与目录统计构建上下文（无模拟数据）。"""
    root = project_root
    settings = root / "config" / "settings"
    context: Dict[str, Any] = {
        "project_root": str(root),
        "environments": [],
        "auth": {},
        "fixtures": {},
        "api_docs": [],
    }

    env_ini = settings / "env_config.ini"
    if env_ini.is_file():
        parser = configparser.ConfigParser()
        parser.read(env_ini, encoding="utf-8")
        for section in parser.sections():
            if section == "database":
                continue
            base_url = parser.get(section, "base_url", fallback="").strip()
            context["environments"].append({"name": section, "base_url": base_url or "获取不到"})

    auth_ini = settings / "auth.ini"
    if auth_ini.is_file():
        parser = configparser.ConfigParser()
        parser.read(auth_ini, encoding="utf-8")
        username = "获取不到"
        if parser.has_option("login", "body"):
            try:
                body = json.loads(parser.get("login", "body"))
                username = body.get("username") or "获取不到"
            except json.JSONDecodeError:
                pass
        context["auth"] = {
            "login_path": parser.get("login", "path", fallback="获取不到"),
            "username": username,
            "enabled": parser.get("auth", "enabled", fallback="获取不到"),
        }

    fixtures = root / "fixtures"
    for suite in ("smoke", "manual", "ai"):
        count = _count_csv_cases(fixtures / suite / "csv")
        context["fixtures"][suite] = count

    api_docs = root / "api_docs"
    if api_docs.is_dir():
        context["api_docs"] = sorted(
            str(path.relative_to(root)).replace("\\", "/")
            for path in api_docs.rglob("*")
            if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml", ".md"}
        )[:20]

    return context


def format_project_context_for_prompt(project_root: Path) -> str:
    """格式化为 Prompt 段落。"""
    ctx = build_project_context(project_root)
    lines = [
        "## 项目上下文（真实配置摘要）",
        f"- 项目根目录: {ctx['project_root']}",
    ]
    if ctx["environments"]:
        lines.append("- 运行环境:")
        for env in ctx["environments"]:
            lines.append(f"  - {env['name']}: {env['base_url']}")
    else:
        lines.append("- 运行环境: 获取不到")

    if ctx["auth"]:
        lines.append(
            f"- 鉴权: login={ctx['auth'].get('login_path')} "
            f"user={ctx['auth'].get('username')} enabled={ctx['auth'].get('enabled')}"
        )
    else:
        lines.append("- 鉴权: 获取不到")

    if ctx["fixtures"]:
        parts = [f"{k}={v if v is not None else '获取不到'}" for k, v in ctx["fixtures"].items()]
        lines.append(f"- 现有用例数: {', '.join(parts)}")

    if ctx["api_docs"]:
        lines.append(f"- API 文档: {', '.join(ctx['api_docs'][:5])}")
    return "\n".join(lines)
