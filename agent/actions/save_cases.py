#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：保存测试用例 Action，将用例写入指定格式文件
创建时间：2026-06-02
"""

import logging
from typing import Any, Dict

from agent.actions.base import Action
from agent.generator.template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class SaveCasesAction(Action):
    """将 context['test_cases'] 保存到 context['output_path']。"""

    name = "save_cases"
    description = "将测试用例格式化为 excel/csv/json 并写入文件"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        test_cases = context.get("test_cases")
        output_path = context.get("output_path")
        output_format = context.get("output_format", "csv")

        if not test_cases:
            raise ValueError("context 缺少 test_cases")
        if not output_path:
            raise ValueError("context 缺少 output_path")

        engine: TemplateEngine = context.get("template_engine") or TemplateEngine()
        success = engine.save_cases_to_file(test_cases, output_path, output_format)

        if not success:
            raise RuntimeError(f"保存测试用例失败: {output_path}")

        context["template_engine"] = engine
        context["saved"] = True
        logger.info("已保存 %d 条用例到 %s", len(test_cases), output_path)
        return context
