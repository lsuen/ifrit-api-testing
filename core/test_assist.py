#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试失败 AI 辅助分析（建议是否留存由用户决定）。"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.llm.client import AIClient
from config.ai_config import AIConfig

logger = logging.getLogger(__name__)

ASSIST_MARKER = "[IFRIT] TEST_ASSIST_JSON="


def _extract_failure_snippets(stdout: str, stderr: str, limit: int = 80) -> List[str]:
    text = f"{stdout}\n{stderr}"
    lines = []
    for line in text.splitlines():
        if re.search(r"FAIL|ERROR|AssertionError|failed|错误", line, re.I):
            lines.append(line.strip())
    if not lines:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()][-limit:]
    return lines[:limit]


def analyze_test_output(
    stdout: str,
    stderr: str,
    run_id: Optional[str] = None,
    suite: Optional[str] = None,
) -> Dict[str, Any]:
    """LLM 分析失败原因，返回结构化建议（不写入磁盘）。"""
    snippets = _extract_failure_snippets(stdout, stderr)
    if not snippets:
        return {
            "summary": "未发现明显失败片段，无需 AI 辅助",
            "diagnosis": [],
            "suggestions": [],
            "save_hint": "无建议可保存",
        }

    ai_config = AIConfig()
    if not ai_config.validate_config():
        raise RuntimeError("AI 配置无效，无法启用测试辅助")

    client = AIClient(ai_config.get_openai_config())
    prompt = f"""你是 API 自动化测试专家。根据以下测试输出片段，输出 JSON（不要其他文字）。

schema:
{{
  "summary": "一段话总结",
  "diagnosis": [{{"case": "用例名或接口", "detail": "失败原因分析", "severity": "high|medium|low"}}],
  "suggestions": [{{"title": "建议标题", "action": "具体修复动作", "retain_default": false}}],
  "save_hint": "若用户要留存，建议保存到哪里/什么格式"
}}

run_id: {run_id or '(未知)'}
suite: {suite or '(未知)'}

失败片段:
{chr(10).join(snippets)}
"""
    response = client.complete(prompt)
    if not response:
        raise RuntimeError(client.last_error or "LLM 无响应")

    text = response.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {
            "summary": response[:500],
            "diagnosis": [],
            "suggestions": [],
            "save_hint": "解析失败，请查看 summary",
        }
    if not isinstance(data, dict):
        data = {"summary": str(data), "diagnosis": [], "suggestions": []}
    data.setdefault("retain_decision", "user")  # 留存交给用户
    return data


def run_test_assist_cli(stdout: str, stderr: str, run_id: str = "", suite: str = "") -> int:
    try:
        result = analyze_test_output(stdout, stderr, run_id=run_id or None, suite=suite or None)
        print(ASSIST_MARKER + json.dumps(result, ensure_ascii=False))
        print(f"[IFRIT] TEST_ASSIST done diagnosis={len(result.get('diagnosis', []))}")
        return 0
    except Exception as error:
        print(f"[IFRIT] TEST_ASSIST failed: {error}")
        return 1


def save_assist_report(project_root: str, run_id: str, payload: Dict[str, Any]) -> str:
    """用户确认留存时写入 reports/runs/<run_id>/ai_assist.json"""
    root = Path(project_root)
    if run_id:
        out_dir = root / "reports" / "runs" / run_id
    else:
        out_dir = root / "reports" / "runs" / "_assist"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ai_assist.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return str(out_path.relative_to(root)).replace("\\", "/")
