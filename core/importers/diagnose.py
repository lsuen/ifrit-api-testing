#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""导入用例 LLM 诊断与补充建议。"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.llm.client import AIClient
from config.ai_config import AIConfig
from core.importers.case_writer import CASE_COLUMNS, normalize_row

logger = logging.getLogger(__name__)

DIAGNOSE_PROMPT = """你是 API 自动化测试专家。请分析以下从 Postman 导入的测试用例，输出 JSON（不要其他文字）。

## 任务
1. diagnosis: 诊断现有用例缺口（如缺少边界值、缺少反向/类型错误用例、断言不足等）
2. suggested_cases: 建议追加的用例（ifrit CSV 字段）

## 输出 JSON  schema
{{
  "diagnosis": [
    {{"category": "missing_boundary|missing_negative|type_error|weak_assertion|other", "endpoint": "/api/...", "detail": "说明", "severity": "high|medium|low"}}
  ],
  "suggested_cases": [
    {{"name": "用例名", "method": "POST", "url": "/api/...", "headers": "{{}}", "params": "{{}}", "body": "{{}}", "expected_status": "400", "expected_result": "", "extract": "", "validate": "", "priority": "1", "enabled": "1", "reason": "追加原因"}}
  ],
  "summary": "一段话总结"
}}

## 约束
- suggested_cases 必须是可追加的新用例，不要重复已有用例
- headers/params/body 必须是 JSON 字符串
- 仅输出 JSON

{project_context}

{rag_context}

## Collection 信息
{meta_json}

## 现有用例（共 {case_count} 条）
{cases_json}
"""


class ImportDiagnosisError(RuntimeError):
    """诊断失败。"""


class ImportDiagnosisService:
    """对导入用例做 LLM 诊断与补用例建议。"""

    def __init__(self):
        ai_config = AIConfig()
        if not ai_config.validate_config():
            raise ImportDiagnosisError("AI 配置无效，请检查 .env 与 config/settings/ai.ini")
        self.client = AIClient(ai_config.get_openai_config())

    def diagnose(
        self,
        rows: List[Dict[str, Any]],
        meta: Optional[Dict[str, Any]] = None,
        project_context: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not rows:
            raise ImportDiagnosisError("没有用例可诊断")

        clean_rows = [{key: row.get(key, "") for key in CASE_COLUMNS} for row in rows]
        prompt = DIAGNOSE_PROMPT.format(
            project_context=project_context or "（未注入项目上下文）",
            rag_context=rag_context or "（未启用知识库 RAG）",
            meta_json=json.dumps(meta or {}, ensure_ascii=False),
            case_count=len(clean_rows),
            cases_json=json.dumps(clean_rows, ensure_ascii=False, indent=2),
        )

        model = getattr(self.client, "model", "")
        logger.info("开始 LLM 导入诊断，用例数=%d model=%s", len(clean_rows), model)
        print(f"[IFRIT] 诊断 LLM model={model} 用例数={len(clean_rows)}")
        response = self.client.complete(prompt)
        if not response:
            detail = getattr(self.client, "last_error", None) or "LLM 返回空响应"
            raise ImportDiagnosisError(detail)

        parsed = self._parse_response(response)
        suggested = []
        for index, item in enumerate(parsed.get("suggested_cases") or [], start=1):
            if not isinstance(item, dict):
                continue
            row = normalize_row(item)
            row["id"] = f"new_{index}"
            row["_source"] = "suggested"
            row["_reason"] = str(item.get("reason", ""))
            suggested.append(row)

        diagnosis = parsed.get("diagnosis") or []
        if not isinstance(diagnosis, list):
            diagnosis = []

        return {
            "diagnosis": diagnosis,
            "suggested_cases": suggested,
            "summary": parsed.get("summary", ""),
            "llm_used": True,
        }

    @staticmethod
    def _parse_response(text: str) -> Dict[str, Any]:
        text = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ImportDiagnosisError(f"LLM 响应非合法 JSON: {error}") from error
        if not isinstance(data, dict):
            raise ImportDiagnosisError("LLM 响应必须是 JSON 对象")
        return data
