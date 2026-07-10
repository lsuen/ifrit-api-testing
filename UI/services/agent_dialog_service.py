#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Agent 对话：自然语言意图 → CLI/Skill 执行计划。"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.cli_runner import (
    build_ai_generate_command,
    build_import_command,
    build_test_command,
)
from services.config_loader import get_remote_swagger_url
from services.ifrit_paths import list_api_docs


def get_agent_context(config: Dict[str, Any]) -> Dict[str, Any]:
    root = config["ifrit"]["root_path_resolved"]
    docs = list_api_docs(config)
    default_doc = docs[0]["relative"] if docs else None
    presets = config.get("presets", {})
    smoke_file = presets.get("smoke_file", "fixtures/smoke/csv/api_test_smoke.csv")
    sample_import = "tests/fixtures/postman/ifrit_address_smoke.postman_collection.json"
    if not (root / sample_import).is_file():
        sample_import = None
    ai_output = "fixtures/ai/csv"
    ai_dir = root / "fixtures" / "ai" / "csv"
    if ai_dir.is_dir():
        try:
            ai_output = str(ai_dir.relative_to(root)).replace("\\", "/")
        except ValueError:
            pass
    return {
        "default_doc": default_doc,
        "swagger_url": get_remote_swagger_url(config),
        "smoke_file": smoke_file,
        "sample_import": sample_import,
        "ai_output_dir": ai_output,
        "import_output": "fixtures/manual/csv/agent_import_run.csv",
    }


def _extract_endpoints(message: str) -> List[str]:
    return list(dict.fromkeys(re.findall(r"/api/[\w./-]+", message)))


def _match_intent(message: str) -> str:
    text = message.strip()
    lower = text.lower()
    if text.startswith("--"):
        return "cli"
    if re.match(r"^(doc|url|help|skills|show|generate|endpoint|format|out|skill)\b", lower):
        return "chat"
    if any(k in text for k in ("导入并", "导入后", "import and", "postman并")):
        return "import_execute"
    if any(k in lower for k in ("postman", "导入")) and any(k in text for k in ("执行", "跑", "测试", "运行")):
        return "import_execute"
    if any(k in lower for k in ("冒烟", "smoke")):
        return "execute_smoke"
    if any(k in text for k in ("执行", "跑测试", "运行测试", "跑通")):
        return "execute"
    if any(k in text for k in ("鉴权", "登录", "token", "auth")):
        return "generate_auth"
    if any(k in text for k in ("生成", "AI", "用例", "generate")):
        return "generate"
    return "generate"


def _rule_skill_hint(intent: str, message: str, endpoints: List[str]) -> Optional[str]:
    if intent == "generate_auth":
        return "鉴权发现与登录流程"
    if endpoints:
        return f"关注端点 {', '.join(endpoints)}"
    if message.strip():
        return message.strip()[:200]
    return None


def preview_skill(config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    root = str(config["ifrit"]["root_path_resolved"])
    if root not in sys.path:
        sys.path.insert(0, root)
    from agent.skills.router import _rule_based_route

    ctx = {
        "input_doc": params.get("input_doc"),
        "input_url": params.get("input_url"),
        "endpoints": params.get("endpoints") or [],
        "user_hint": params.get("skill_hint") or "",
    }
    routed = _rule_based_route(ctx)
    return {
        "skill_name": routed.get("skill_name"),
        "reason": routed.get("reason"),
        "source": "rule",
    }


def build_agent_plan(config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    message = (data.get("message") or "").strip()
    form = data.get("form") or {}
    ctx = get_agent_context(config)
    intent = form.get("intent") or _match_intent(message)
    endpoints = form.get("endpoints") or _extract_endpoints(message)
    if isinstance(endpoints, str):
        endpoints = [e.strip() for e in endpoints.split("\n") if e.strip()]

    use_rag = bool(form.get("rag"))
    auto_skill = form.get("no_auto_skill") is not True
    skill = (form.get("skill") or "").strip() or None
    skill_hint = (form.get("skill_hint") or "").strip() or _rule_skill_hint(intent, message, endpoints)

    input_doc = form.get("input_doc") or ctx["default_doc"]
    input_url = form.get("input_url") or (ctx["swagger_url"] if not input_doc else None)
    output_dir = form.get("output_dir") or ctx["ai_output_dir"]

    steps: List[Dict[str, Any]] = []
    summary = ""

    if intent == "cli":
        line = message if message.startswith("--") else form.get("cli_line", message)
        summary = f"执行 CLI：{line[:80]}"
        steps.append({"type": "cli", "label": "CLI", "line": line})

    elif intent == "chat":
        line = message or form.get("chat_line", "")
        summary = f"Chat 命令：{line[:80]}"
        steps.append({"type": "chat", "label": "Chat", "tokens": line.split()})

    elif intent == "execute_smoke":
        summary = "执行冒烟用例并生成报告"
        params = {
            "file": ctx["smoke_file"],
            "global_auth": True,
            "generate_report": True,
        }
        steps.append({"type": "execute", "label": "冒烟测试", "params": params})

    elif intent == "execute":
        suite = form.get("suite") or "ai"
        summary = f"执行 {suite} 套件并生成报告"
        params = {
            "suite": suite,
            "type": form.get("test_type") or "csv",
            "global_auth": form.get("global_auth", True),
            "generate_report": True,
        }
        if form.get("file"):
            params = {
                "file": form["file"],
                "global_auth": form.get("global_auth", True),
                "generate_report": True,
            }
        steps.append({"type": "execute", "label": "执行测试", "params": params})

    elif intent == "import_execute":
        import_file = form.get("import_file") or ctx["sample_import"]
        if not import_file:
            raise ValueError("无可用 Postman 样例，请在导入中心上传或指定 import_file")
        output = form.get("import_output") or ctx["import_output"]
        summary = "导入 Postman → 执行用例 → 生成报告"
        steps.append(
            {
                "type": "import",
                "label": "导入 Postman",
                "params": {
                    "import_file": import_file,
                    "format": "postman",
                    "suite": "manual",
                    "output_format": "csv",
                    "output": output,
                },
            }
        )
        steps.append(
            {
                "type": "execute",
                "label": "执行导入用例",
                "params": {
                    "file": output,
                    "global_auth": True,
                    "generate_report": True,
                },
                "after_import": True,
            }
        )
        steps.append({"type": "rag_ingest", "label": "写入知识库", "path_from": "import_output"})

    else:
        if not input_doc and not input_url:
            raise ValueError("请提供文档路径/URL，或在 api_docs 放置 Swagger JSON")
        summary = "AI 生成用例（自动 Skill 路由）"
        gen_params: Dict[str, Any] = {
            "format": form.get("format") or "csv",
            "output_dir": output_dir,
            "endpoints": endpoints,
            "rag": use_rag,
            "no_auto_skill": not auto_skill,
        }
        if skill:
            gen_params["skill"] = skill
        if skill_hint:
            gen_params["skill_hint"] = skill_hint
        if input_url and form.get("source") == "url":
            gen_params["input_url"] = input_url
        elif input_url and not input_doc:
            gen_params["input_url"] = input_url
        else:
            gen_params["input_doc"] = input_doc
        steps.append({"type": "generate", "label": "AI 生成", "params": gen_params})
        if form.get("run_after"):
            steps.append(
                {
                    "type": "execute",
                    "label": "执行 AI 用例",
                    "params": {
                        "suite": "ai",
                        "type": "csv",
                        "global_auth": True,
                        "generate_report": True,
                    },
                }
            )
        steps.append({"type": "rag_ingest", "label": "写入知识库", "path_from": "generate_output"})

    skill_preview = None
    if steps and steps[0].get("type") == "generate":
        p = steps[0]["params"]
        try:
            skill_preview = preview_skill(
                config,
                {
                    "input_doc": p.get("input_doc"),
                    "input_url": p.get("input_url"),
                    "endpoints": p.get("endpoints"),
                    "skill_hint": p.get("skill_hint"),
                },
            )
        except Exception:
            skill_preview = None

    return {
        "intent": intent,
        "summary": summary,
        "steps": steps,
        "skill_preview": skill_preview,
        "context": ctx,
    }


def build_step_command(config: Dict[str, Any], step: Dict[str, Any]) -> List[str]:
    step_type = step.get("type")
    if step_type == "execute":
        return build_test_command(config, step.get("params") or {})
    if step_type == "generate":
        return build_ai_generate_command(config, step.get("params") or {})
    if step_type == "import":
        return build_import_command(config, step.get("params") or {})
    if step.get("command"):
        return step["command"]
    raise ValueError(f"无法构建步骤命令: {step_type}")
