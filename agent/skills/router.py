#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 路由：Function Calling 自动匹配可执行 Skill。"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.skills.catalog import build_catalog
from agent.skills.paths import SkillStorePaths
from agent.skills.registry import get_skill_detail, list_skills, list_skills_detail

logger = logging.getLogger(__name__)

SELECT_SKILL_TOOL_NAME = "select_ifrit_skill"


def _emit(message: str, sink=None) -> None:
    if sink:
        sink(message)
    else:
        print(message, flush=True)


def build_skill_tool_schema(skill_names: List[str]) -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": SELECT_SKILL_TOOL_NAME,
                "description": (
                    "根据用户任务从 ifrit 内置可执行 Skill 中选择最合适的一个。"
                    "仅返回 skill_name，必须来自枚举列表。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "enum": skill_names,
                            "description": "要执行的内置 skill 名称",
                        },
                        "reason": {
                            "type": "string",
                            "description": "选择理由（简短中文）",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "0-1 置信度",
                        },
                    },
                    "required": ["skill_name", "reason"],
                },
            },
        }
    ]


def collect_router_context(project_root: Optional[str] = None) -> Dict[str, Any]:
    """汇总内置 + 已启用库技能，供路由提示词使用。"""
    builtins = list_skills_detail()
    library: List[Dict[str, Any]] = []
    if project_root:
        paths = SkillStorePaths(project_root)
        for item in build_catalog(paths):
            if item.enabled:
                library.append(item.to_dict())
    return {"builtin": builtins, "library_enabled": library}


def _rule_based_route(context: Dict[str, Any]) -> Dict[str, Any]:
    if context.get("input_url"):
        skill = "doc_url_generation"
        reason = "检测到 input_url，使用远程文档拉取流水线"
    elif context.get("endpoints") and len(context.get("endpoints") or []) == 1:
        skill = "parse_only"
        reason = "仅指定单个端点预览，使用 parse_only"
    elif context.get("intent") == "auth":
        skill = "auth_discovery"
        reason = "鉴权发现任务"
    elif context.get("intent") == "probe":
        skill = "endpoint_probe"
        reason = "端点探测任务"
    elif context.get("intent") == "quality":
        skill = "ai_quality_loop"
        reason = "质量闭环任务"
    else:
        skill = "case_generation"
        reason = "默认本地文档生成用例"
    return {
        "skill_name": skill,
        "reason": reason,
        "confidence": 0.6,
        "source": "rule",
        "tool_name": None,
    }


def route_skill(
    client,
    context: Dict[str, Any],
    project_root: Optional[str] = None,
    event_sink=None,
) -> Dict[str, Any]:
    """
    使用 Function Calling 选择 skill；失败则规则降级。

    context 可含: input_doc, input_url, endpoints, intent, user_hint
    """
    skill_names = list_skills()
    if not skill_names:
        raise RuntimeError("无可用内置 skill")

    catalog = collect_router_context(project_root)
    user_hint = context.get("user_hint") or ""
    endpoints = context.get("endpoints") or []

    system = (
        "你是 ifrit API 测试平台的 Skill 路由器。"
        "必须调用 select_ifrit_skill 选择一个内置 skill。"
        "规则提示：有 input_url 优先 doc_url_generation；"
        "仅解析文档用 parse_only；鉴权发现 auth_discovery；"
        "探测 endpoint_probe；完整质量闭环 ai_quality_loop；"
        "默认本地 Swagger 生成 case_generation。"
    )
    user_parts = [
        f"input_doc: {context.get('input_doc') or '(无)'}",
        f"input_url: {context.get('input_url') or '(无)'}",
        f"endpoints: {endpoints or '(全部)'}",
        f"user_hint: {user_hint or '(无)'}",
        f"builtin_skills: {json.dumps(catalog['builtin'], ensure_ascii=False)}",
    ]
    if catalog["library_enabled"]:
        user_parts.append(
            f"enabled_library_skills(参考，不可执行): "
            f"{json.dumps(catalog['library_enabled'], ensure_ascii=False)}"
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
    tools = build_skill_tool_schema(skill_names)

    _emit("[IFRIT] SKILL_ROUTE start function_calling=true", event_sink)

    try:
        result = client.chat_with_tools(messages, tools=tools, tool_choice="auto")
        tool_calls = result.get("tool_calls") or []
        for call in tool_calls:
            if call.get("name") != SELECT_SKILL_TOOL_NAME:
                continue
            args = call.get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
            skill_name = args.get("skill_name")
            if skill_name not in skill_names:
                continue
            routed = {
                "skill_name": skill_name,
                "reason": args.get("reason", ""),
                "confidence": float(args.get("confidence", 0.8)),
                "source": "function_calling",
                "tool_name": SELECT_SKILL_TOOL_NAME,
            }
            _emit(
                f"[IFRIT] SKILL_ROUTE tool={SELECT_SKILL_TOOL_NAME} "
                f"skill={skill_name} confidence={routed['confidence']:.2f} "
                f"reason={routed['reason']}",
                event_sink,
            )
            detail = get_skill_detail(skill_name)
            _emit(
                f"[IFRIT] SKILL_MATCH skill={skill_name} "
                f"actions={','.join(detail.get('action_names', []))}",
                event_sink,
            )
            return routed
    except Exception as error:
        logger.warning("Function calling 路由失败，降级规则: %s", error)
        _emit(f"[IFRIT] SKILL_ROUTE fallback reason={error}", event_sink)

    routed = _rule_based_route(context)
    _emit(
        f"[IFRIT] SKILL_ROUTE source=rule skill={routed['skill_name']} reason={routed['reason']}",
        event_sink,
    )
    detail = get_skill_detail(routed["skill_name"])
    _emit(
        f"[IFRIT] SKILL_MATCH skill={routed['skill_name']} "
        f"actions={','.join(detail.get('action_names', []))}",
        event_sink,
    )
    return routed
