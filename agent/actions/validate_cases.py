#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：用例质量验证 Action，批量校验并写入验证结果
创建时间：2026-06-02
"""

import logging
from typing import Any, Dict

from agent.actions.base import Action
from agent.generator.quality_validator import QualityValidator

logger = logging.getLogger(__name__)


class ValidateCasesAction(Action):
    """验证 context['test_cases']，结果写入 context['validation_result']。"""

    name = "validate_cases"
    description = "批量验证测试用例质量与逻辑一致性"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        test_cases = context.get("test_cases")
        if not test_cases:
            raise ValueError("context 缺少 test_cases，请先执行 generate_cases")

        if not context.get("quality_check", True):
            logger.info("已跳过质量验证（quality_check=False）")
            return context

        validator: QualityValidator = context.get("validator") or QualityValidator()
        result = validator.validate_batch_cases(test_cases)

        context["validator"] = validator
        context["validation_result"] = result

        if result["invalid_cases"] > 0:
            logger.warning("发现 %d 条无效用例", result["invalid_cases"])

        quality_score = validator.get_quality_score(result)
        context["quality_score"] = quality_score
        logger.info(
            "质量评分: %s (%s) - %s",
            quality_score["score"],
            quality_score["grade"],
            quality_score["description"],
        )
        return context
