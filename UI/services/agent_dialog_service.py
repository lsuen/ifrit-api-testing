#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Agent 对话：自然语言意图 → CLI/Skill 执行计划或对话引导。"""
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

AGENT_NAME = "ifrit 接口自动化测试助手"

SUGGESTED_PROMPTS = [
    "跑冒烟测试并出报告",
    "生成 /api/address 用例",
    "导入 Postman 并执行",
    "如何配置鉴权和环境？",
]

_GREETING_RE = re.compile(
    r"^(你好|您好|嗨|哈喽|hello|hi|hey|在吗|早上好|下午好|晚上好)[!?。，~]*$",
    re.I,
)
_THANKS_RE = re.compile(r"^(谢谢|感谢|thanks|thx)[你您]?[!?。~]*", re.I)
_HELP_RE = re.compile(
    r"(你是谁|你能做什么|你会什么|怎么用|如何使用|怎么开始|帮助|help|"
    r"是什么|什么意思|如何配置|怎么配|入门|新手|文档|手册)",
    re.I,
)
_TASK_KEYWORDS = (
    "跑", "执行", "运行", "测试", "生成", "导入", "postman", "冒烟", "smoke",
    "generate", "鉴权", "auth", "用例", "报告", "doc ", "url ", "--",
)


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


def _has_task_intent(message: str) -> bool:
    if _HELP_RE.search(message):
        return False
    text = message.strip().lower()
    if text.startswith("--"):
        return True
    if re.match(r"^(doc|url|generate|endpoint|skill)\b", text):
        return True
    if _extract_endpoints(message):
        return True
    return any(k in message for k in _TASK_KEYWORDS) or any(k in text for k in ("postman", "smoke"))


def _is_conversational(message: str) -> bool:
    text = message.strip()
    if not text:
        return True
    if _has_task_intent(text):
        return False
    if _GREETING_RE.match(text) or _THANKS_RE.match(text) or _HELP_RE.search(text):
        return True
    if len(text) <= 16:
        return True
    return False


def _static_conversational_reply(message: str, ctx: Dict[str, Any]) -> str:
    text = message.strip()
    if _GREETING_RE.match(text):
        return (
            f"你好！我是 **{AGENT_NAME}**。\n\n"
            "我可以帮你：\n"
            "· 跑冒烟 / 执行用例 / 生成报告\n"
            "· 从 Swagger 文档 AI 生成用例\n"
            "· 导入 Postman 并一键执行\n"
            "· 解答项目配置与使用问题（环境、鉴权、RAG 等）\n\n"
            "试试说：「跑冒烟测试」或「如何配置鉴权？」"
        )
    if _THANKS_RE.match(text):
        return "不客气！有需要随时说，或点左侧快捷意图按钮。"
    if _HELP_RE.search(text):
        doc_hint = ctx.get("default_doc") or "api_docs 下的 Swagger JSON"
        return (
            f"**快速上手（Web UI）**\n"
            "1. **设置** — 填环境、鉴权、AI，跑就绪检查\n"
            "2. **仪表盘** — 一键「冒烟全流程」或「导入→执行」\n"
            "3. **报告** — 查看 HTML 结果\n\n"
            f"**CLI 等价**：`python main.py --file fixtures/smoke/csv/api_test_smoke.csv`\n\n"
            f"**AI 生成**：需要 {doc_hint}，说「生成 /api/xxx 用例」即可。\n"
            "**鉴权**：`config/settings/auth.ini` + 执行时勾选全局鉴权。\n\n"
            "更完整说明见侧栏 **关于** 或仓库内《用户详细使用手册》。"
        )
    return (
        f"我是 **{AGENT_NAME}**。若要做测试，请说具体任务，例如：\n"
        "· 跑冒烟测试并出报告\n"
        "· 生成地址接口用例\n"
        "· 导入 Postman 并执行\n\n"
        "若是配置/使用问题，可以直接问「如何配置环境」等。"
    )


def generate_conversational_reply(config: Dict[str, Any], message: str) -> Dict[str, Any]:
    from services.settings_service import _reload_project_env, get_effective_ai_config

    ctx = get_agent_context(config)
    static_text = _static_conversational_reply(message, ctx)
    llm_error = ""

    root = config["ifrit"]["root_path_resolved"]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        _reload_project_env(config)
        from config.ai_config import AIConfig
        from agent.llm.client import AIClient

        effective = get_effective_ai_config(config)
        ai_config = AIConfig()
        if not ai_config.validate_config():
            raise RuntimeError("AI 配置校验失败，请检查设置页")

        openai_cfg = ai_config.get_openai_config()
        client = AIClient(openai_cfg)
        system = (
            f"你是 {AGENT_NAME}，语气自然、像同事一样交流，不要像机器人列清单。"
            "你熟悉 ifrit-apitest：接口自动化、冒烟、Postman 导入、Swagger AI 生成、全局鉴权、报告、知识库 RAG。"
            "Web：设置 /settings、仪表盘 /、导入 /import、AI /ai、执行 /execute、报告 /reports、Agent /agent。"
            "规则：用户闲聊就友好回应并简短介绍你能做什么；问用法就给 2～4 步可操作建议；"
            "不要假装已经在跑测试；只有用户明确下任务时才提醒可以说「跑冒烟」等。"
            f"\n当前项目：文档={ctx.get('default_doc') or '无'}，冒烟={ctx.get('smoke_file')}。"
            f"\n当前 LLM：{effective.get('base_url')} / {effective.get('model')}。"
        )
        llm_text = client.chat_simple(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": message.strip()},
            ],
            max_retries=2,
            max_tokens=800,
        )
        if llm_text:
            return {
                "text": llm_text,
                "source": "llm",
                "suggestions": SUGGESTED_PROMPTS,
                "llm_endpoint": effective.get("base_url"),
                "llm_model": effective.get("model"),
            }
        llm_error = client.last_error or "LLM 无响应"
    except Exception as error:
        llm_error = str(error)

    fallback = static_text.replace("**", "")
    if llm_error:
        fallback += f"\n\n（LLM 未连通：{llm_error}。请到 **设置 → AI/LLM** 检查 Base URL 与 Model，并勾选「测试 LLM 连通」。）"
    return {
        "text": fallback,
        "source": "static",
        "suggestions": SUGGESTED_PROMPTS,
        "llm_error": llm_error,
    }


def _match_intent(message: str) -> str:
    text = message.strip()
    lower = text.lower()
    if _is_conversational(text):
        return "converse"
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
    if _extract_endpoints(text):
        return "generate"
    return "converse"


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

    if intent == "converse":
        reply = generate_conversational_reply(config, message)
        return {
            "intent": "converse",
            "mode": "converse",
            "summary": "对话",
            "steps": [],
            "reply": reply["text"],
            "reply_source": reply["source"],
            "llm_error": reply.get("llm_error"),
            "suggestions": reply.get("suggestions", SUGGESTED_PROMPTS),
            "context": ctx,
        }

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
        "mode": "execute",
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
