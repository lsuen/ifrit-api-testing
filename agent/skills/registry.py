#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：Skill 注册表，按名称加载预定义的 Action 集合
创建时间：2026-06-02
"""

from typing import Dict, List

from agent.actions.base import Action
from agent.actions.fetch_document import FetchDocumentAction
from agent.actions.parse_document import ParseDocumentAction
from agent.actions.generate_cases import GenerateCasesAction
from agent.actions.validate_cases import ValidateCasesAction
from agent.actions.save_cases import SaveCasesAction
from agent.actions.probe_endpoint import ProbeEndpointAction
from agent.actions.discover_auth import DiscoverAuthAction
from agent.actions.prune_failed_cases import PruneFailedCasesAction

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


def register_skill(name: str, actions: List[Action]) -> None:
    """注册或覆盖一个 skill 的 Action 集合。"""
    _SKILL_ACTIONS[name] = actions


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
