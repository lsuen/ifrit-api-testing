#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""控制台命令校验与构建。"""
import shlex
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from services.config_loader import load_config


def _policy_path() -> Path:
    return load_config()["ifrit"]["root_path_resolved"] / "config" / "console_policy.yaml"


def load_console_policy() -> Dict[str, Any]:
    policy_path = _policy_path()
    if not policy_path.is_file():
        return {}
    with open(policy_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}

def validate_console_line(mode: str, line: str) -> Tuple[bool, str, str]:
    """
    校验控制台输入。

    Returns:
        (ok, level, message)  level: ok | warn | block
    """
    line = (line or "").strip()
    if not line:
        return False, "block", "命令不能为空"

    policy = load_console_policy()
    blocked = policy.get("blocked_substrings") or []
    for frag in blocked:
        if frag in line:
            return False, "block", f"命令包含禁止片段: {frag}"

    warned = policy.get("warn_substrings") or []
    warn_hit = next((w for w in warned if w in line.lower()), None)

    if mode == "cli":
        if policy.get("cli_mode", {}).get("require_double_dash_prefix", True):
            if not line.startswith("--"):
                return False, "block", "CLI 模式参数须以 -- 开头"
        try:
            shlex.split(line)
        except ValueError as error:
            return False, "block", f"参数解析失败: {error}"
    elif mode == "chat":
        try:
            tokens = shlex.split(line)
        except ValueError as error:
            return False, "block", f"参数解析失败: {error}"
        if not tokens:
            return False, "block", "命令不能为空"
        allowed = policy.get("chat_mode", {}).get("allowed_commands") or []
        if tokens[0].lower() not in allowed:
            return False, "block", f"不允许的 chat 子命令: {tokens[0]}"
    else:
        return False, "block", f"未知模式: {mode}"

    if warn_hit:
        return True, "warn", f"警告: 命令包含敏感操作 ({warn_hit})，请确认"
    return True, "ok", ""


def build_main_command(python: str, main_script: str, mode: str, line: str) -> List[str]:
    line = line.strip()
    if mode == "cli":
        return [python, main_script] + shlex.split(line)
    if mode == "chat":
        return [python, main_script, "--chat"] + shlex.split(line)
    raise ValueError(f"未知模式: {mode}")


def build_help_command(python: str, main_script: str, mode: str) -> List[str]:
    if mode == "chat":
        return [python, main_script, "--chat", "help"]
    return [python, main_script, "--help"]
