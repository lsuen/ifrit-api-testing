#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：AI 生成测试用例 Action，遍历 API 列表批量生成用例
创建时间：2026-06-02
"""

import logging
from typing import Any, Dict, List

from agent.actions.base import Action
from agent.generator.case_generator import CaseGenerator

logger = logging.getLogger(__name__)


class GenerateCasesAction(Action):
    """为 context['apis'] 中每个接口生成测试用例，写入 context['test_cases']。"""

    name = "generate_cases"
    description = "调用 LLM 为每个 API 生成多类型测试用例"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        apis = context.get("apis")
        if not apis:
            raise ValueError("context 缺少 apis，请先执行 parse_document")

        generator: CaseGenerator = context.get("generator")
        if generator is None:
            raise ValueError("context 缺少 generator（CaseGenerator 实例）")

        all_cases: List[Dict[str, Any]] = []
        for api in apis:
            logger.info("生成用例: %s %s", api["method"], api["path"])
            cases = generator.generate_all_cases(api)
            all_cases.extend(cases)

        if not all_cases:
            raise ValueError("未能生成任何测试用例")

        context["test_cases"] = all_cases
        logger.info("共生成 %d 条测试用例", len(all_cases))
        return context
