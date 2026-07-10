#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：Skill 注册表，按名称加载预定义的 Action 集合
创建时间：2026-06-02
"""

from typing import Any, Dict, List, Optional

from agent.actions.base import Action
from agent.actions.fetch_document import FetchDocumentAction
from agent.actions.parse_document import ParseDocumentAction
from agent.actions.generate_cases import GenerateCasesAction
from agent.actions.validate_cases import ValidateCasesAction
from agent.actions.save_cases import SaveCasesAction
from agent.actions.probe_endpoint import ProbeEndpointAction
from agent.actions.discover_auth import DiscoverAuthAction
from agent.actions.prune_failed_cases import PruneFailedCasesAction

# 内置 skill 说明（UI / 日志展示）
_SKILL_META: Dict[str, Dict[str, str]] = {
    "case_generation": {
        "description": "解析本地文档 → 生成 → 校验 → 保存",
        "source": "builtin",
    },
    "doc_url_generation": {
        "description": "拉取远程文档 → 解析 → 生成 → 校验 → 保存",
        "source": "builtin",
    },
    "parse_only": {"description": "仅解析 Swagger/Markdown 文档", "source": "builtin"},
    "generate_and_validate": {
        "description": "解析 → 生成 → 校验（不保存）",
        "source": "builtin",
    },
    "auth_discovery": {"description": "从 Swagger 发现鉴权并更新 auth.ini", "source": "builtin"},
    "endpoint_probe": {"description": "HTTP 探测端点可达性", "source": "builtin"},
    "ai_quality_loop": {
        "description": "探测 → 生成 → 校验 → 保存 → 修剪失败用例",
        "source": "builtin",
    },
}

# 预置 skill：名称 -> Action 列表
_SKILL_ACTIONS: Dict[str, List[Action]] = {
    "case_generation": [
        ParseDocumentAction(),
        GenerateCasesAction(),
        ValidateCasesAction(),
        SaveCasesAction(),
    ],
    "doc_url_generation": [
        FetchDocumentAction(),
        ParseDocumentAction(),
        GenerateCasesAction(),
        ValidateCasesAction(),
        SaveCasesAction(),
    ],
    "parse_only": [
        ParseDocumentAction(),
    ],
    "generate_and_validate": [
        ParseDocumentAction(),
        GenerateCasesAction(),
        ValidateCasesAction(),
    ],
    "auth_discovery": [
        DiscoverAuthAction(),
    ],
    "endpoint_probe": [
        ProbeEndpointAction(),
    ],
    "ai_quality_loop": [
        ProbeEndpointAction(),
        ParseDocumentAction(),
        GenerateCasesAction(),
        ValidateCasesAction(),
        SaveCasesAction(),
        PruneFailedCasesAction(),
    ],
}

_ACTION_REGISTRY: Dict[str, type] = {
    "fetch_document": FetchDocumentAction,
    "parse_document": ParseDocumentAction,
    "generate_cases": GenerateCasesAction,
    "validate_cases": ValidateCasesAction,
    "save_cases": SaveCasesAction,
    "probe_endpoint": ProbeEndpointAction,
    "discover_auth": DiscoverAuthAction,
    "prune_failed_cases": PruneFailedCasesAction,
}


def register_skill(name: str, actions: List[Action], description: str = "") -> None:
    """注册或覆盖一个 skill 的 Action 集合。"""
    _SKILL_ACTIONS[name] = actions
    if description:
        _SKILL_META.setdefault(name, {})["description"] = description
        _SKILL_META[name]["source"] = _SKILL_META.get(name, {}).get("source", "custom")


def get_actions(name: str) -> List[Action]:
    """
    按 skill 名称获取 Action 列表。

    Raises:
        KeyError: skill 不存在
    """
    if name not in _SKILL_ACTIONS:
        available = ", ".join(sorted(_SKILL_ACTIONS.keys()))
        raise KeyError(f"未知 skill: {name}，可用: {available}")
    return list(_SKILL_ACTIONS[name])


def list_skills() -> List[str]:
    """返回已注册的 skill 名称列表。"""
    return sorted(_SKILL_ACTIONS.keys())


def list_action_names() -> List[str]:
    return sorted(_ACTION_REGISTRY.keys())


def get_skill_detail(name: str) -> Dict[str, Any]:
    """返回 skill 元数据与 action 链（供 UI / 日志）。"""
    actions = get_actions(name)
    meta = _SKILL_META.get(name, {})
    return {
        "name": name,
        "description": meta.get("description", ""),
        "source": meta.get("source", "builtin"),
        "actions": [{"name": a.name, "description": a.description} for a in actions],
        "action_names": [a.name for a in actions],
    }


def list_skills_detail() -> List[Dict[str, Any]]:
    return [get_skill_detail(name) for name in list_skills()]


def build_actions_from_names(names: List[str]) -> List[Action]:
    actions: List[Action] = []
    for name in names:
        cls = _ACTION_REGISTRY.get(name)
        if not cls:
            raise KeyError(f"未知 action: {name}")
        actions.append(cls())
    return actions
