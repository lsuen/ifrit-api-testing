#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：简单 ReAct 循环，按序执行 Action 列表并传递 context
创建时间：2026-06-02
"""

import logging
from typing import Any, Dict, List, Optional

from agent.actions.base import Action

logger = logging.getLogger(__name__)


class ReActLoop:
    """按顺序执行 Action 列表，每步将 context 传给下一个 Action。"""

    def __init__(self, actions: List[Action]):
        self.actions = actions

    def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行全部 Action。

        Args:
            context: 初始上下文，默认为空字典

        Returns:
            最终上下文
        """
        ctx = context if context is not None else {}

        for action in self.actions:
            logger.info("执行 Action: %s - %s", action.name, action.description)
            ctx = action.run(ctx)

        return ctx
