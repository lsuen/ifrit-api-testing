#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：Agent Action 基类，定义 name / description / run(context) 契约
创建时间：2026-06-02
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Action(ABC):
    """可注册、可组合的 Agent 原子动作。"""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行动作并返回更新后的上下文。

        Args:
            context: 流水线共享上下文字典

        Returns:
            更新后的上下文
        """
