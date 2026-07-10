#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：ReAct 循环 — Loop Engineering：顺序执行 Action，流式事件输出
创建时间：2026-06-02
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from agent.actions.base import Action

logger = logging.getLogger(__name__)

EventSink = Callable[[str], None]


def _default_sink(message: str) -> None:
    if message.startswith("[IFRIT]"):
        print(message, flush=True)


class ReActLoop:
    """按顺序执行 Action 列表，每步将 context 传给下一个 Action。"""

    def __init__(
        self,
        actions: List[Action],
        skill_name: Optional[str] = None,
        event_sink: Optional[EventSink] = None,
    ):
        self.actions = actions
        self.skill_name = skill_name or ""
        self.event_sink = event_sink or _default_sink

    def _emit(self, message: str) -> None:
        logger.info(message.replace("[IFRIT] ", "", 1) if message.startswith("[IFRIT]") else message)
        self.event_sink(message)

    def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context if context is not None else {}
        total = len(self.actions)
        action_names = ",".join(a.name for a in self.actions)

        self._emit(
            f"[IFRIT] SKILL_MATCH skill={self.skill_name} steps={total} actions={action_names}"
        )

        for index, action in enumerate(self.actions, start=1):
            started = time.time()
            self._emit(
                f"[IFRIT] LOOP step={index}/{total} action={action.name} skill={self.skill_name}"
            )
            try:
                ctx = action.run(ctx)
                elapsed = time.time() - started
                self._emit(
                    f"[IFRIT] LOOP step={index}/{total} action={action.name} status=ok "
                    f"elapsed={elapsed:.2f}s"
                )
            except Exception as error:
                elapsed = time.time() - started
                self._emit(
                    f"[IFRIT] LOOP step={index}/{total} action={action.name} status=error "
                    f"elapsed={elapsed:.2f}s error={error}"
                )
                raise

        self._emit(f"[IFRIT] LOOP complete skill={self.skill_name} steps={total}")
        return ctx
