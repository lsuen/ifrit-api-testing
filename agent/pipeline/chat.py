#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：AI 交互模式（REPL + 单行命令），调度 ReAct Skill 生成用例
"""
import argparse
import logging
import shlex
from typing import Any, Dict, List, Optional

from agent.pipeline.generator import AIGenerator
from agent.skills.registry import list_skills

logger = logging.getLogger(__name__)

HELP_TEXT = """
[IFRIT] AI 交互命令:
  help                         显示帮助
  skills                       列出可用 skill
  doc <path>                   设置本地文档
  url <http(s)://...>          设置远程文档 URL
  endpoint <path>              追加端点过滤（可多次）
  clear-endpoints              清空端点过滤
  format csv|excel|json        设置输出格式
  out <dir>                    设置输出目录
  skill <name>                 设置 skill
  show                         显示当前会话配置
  generate                     执行 AI 生成
  exit | quit                  退出

单行模式示例:
  python main.py --chat -- doc api_docs/apispec_1.json endpoint /api/address generate
"""


class AIChatSession:
    """AI 用例生成交互会话。"""

    def __init__(self, project_root: str = ".", skill_hint: Optional[str] = None, use_rag: bool = False):
        self.project_root = project_root
        self.skill_hint = skill_hint
        self.use_rag = use_rag
        self.state: Dict[str, Any] = {
            "input_doc": None,
            "input_url": None,
            "swagger_endpoint": [],
            "output_format": "csv",
            "output_dir": None,
            "skill": None,
        }

    def run(self, argv: Optional[List[str]] = None) -> int:
        """运行交互或单行命令模式。"""
        if argv:
            return self._run_commands(argv)

        print("[IFRIT] 进入 AI 交互模式，输入 help 查看命令，exit 退出")
        while True:
            try:
                line = input("ifrit> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[IFRIT] 已退出")
                return 0
            if not line:
                continue
            if line in ("exit", "quit"):
                print("[IFRIT] 已退出")
                return 0
            code = self._run_commands(shlex.split(line))
            if code != 0 and line.split()[0] not in ("help", "show", "skills"):
                return code
        return 0

    def _run_commands(self, tokens: List[str]) -> int:
        index = 0
        while index < len(tokens):
            command = tokens[index].lower()
            if command == "help":
                print(HELP_TEXT.strip())
            elif command == "skills":
                print("[IFRIT] skills=" + ", ".join(list_skills()))
            elif command == "doc":
                index = self._require_value(tokens, index, "doc")
                self.state["input_doc"] = tokens[index]
                self.state["input_url"] = None
                print(f"[IFRIT] input_doc={self.state['input_doc']}")
            elif command == "url":
                index = self._require_value(tokens, index, "url")
                self.state["input_url"] = tokens[index]
                self.state["input_doc"] = None
                print(f"[IFRIT] input_url={self.state['input_url']}")
            elif command in ("endpoint", "swagger-endpoint"):
                index = self._require_value(tokens, index, "endpoint")
                self.state["swagger_endpoint"].append(tokens[index])
                print(f"[IFRIT] endpoints={self.state['swagger_endpoint']}")
            elif command == "clear-endpoints":
                self.state["swagger_endpoint"] = []
                print("[IFRIT] endpoints=[]")
            elif command == "format":
                index = self._require_value(tokens, index, "format")
                self.state["output_format"] = tokens[index]
                print(f"[IFRIT] output_format={self.state['output_format']}")
            elif command == "out":
                index = self._require_value(tokens, index, "out")
                self.state["output_dir"] = tokens[index]
                print(f"[IFRIT] output_dir={self.state['output_dir']}")
            elif command == "skill":
                index = self._require_value(tokens, index, "skill")
                self.state["skill"] = tokens[index]
                print(f"[IFRIT] skill={self.state['skill']}")
            elif command == "show":
                self._print_state()
            elif command == "generate":
                return self._generate()
            else:
                print(f"[IFRIT] 未知命令: {command}，输入 help 查看")
                return 1
            index += 1
        return 0

    @staticmethod
    def _require_value(tokens: List[str], index: int, name: str) -> int:
        if index + 1 >= len(tokens):
            raise ValueError(f"命令 {name} 缺少参数")
        return index + 1

    def _print_state(self) -> None:
        print("[IFRIT] ── 会话配置 ──")
        for key in (
            "input_doc",
            "input_url",
            "swagger_endpoint",
            "output_format",
            "output_dir",
            "skill",
        ):
            print(f"[IFRIT] {key}={self.state.get(key)}")

    def _build_args(self) -> argparse.Namespace:
        if not self.state.get("input_doc") and not self.state.get("input_url"):
            raise ValueError("请先 doc <path> 或 url <url>")

        return argparse.Namespace(
            ai_generate=True,
            input_doc=self.state.get("input_doc"),
            input_url=self.state.get("input_url"),
            swagger_endpoint=self.state.get("swagger_endpoint") or None,
            output_format=self.state.get("output_format") or "csv",
            output_dir=self.state.get("output_dir"),
            skill=self.state.get("skill"),
            auto_skill=True,
            skill_hint=self.skill_hint,
            project_root=self.project_root,
            rag=self.use_rag,
        )

    def _generate(self) -> int:
        try:
            args = self._build_args()
        except ValueError as error:
            print(f"[IFRIT] {error}")
            return 1

        generator = AIGenerator(skill_name=args.skill)
        return generator.run(args)


def run_chat_from_argv(extra_argv: Optional[List[str]] = None) -> int:
    """供 CLI 调用的入口。"""
    session = AIChatSession()
    return session.run(extra_argv)
