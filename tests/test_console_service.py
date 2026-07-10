#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""控制台命令策略单元测试。"""
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "UI")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if UI_DIR not in sys.path:
    sys.path.insert(0, UI_DIR)

from services.console_service import build_help_command, build_main_command, validate_console_line


class TestConsoleService(unittest.TestCase):
    def test_cli_requires_double_dash(self):
        ok, level, _ = validate_console_line("cli", "file foo.csv")
        self.assertFalse(ok)
        self.assertEqual(level, "block")

    def test_cli_valid_args(self):
        ok, level, _ = validate_console_line("cli", "--help")
        self.assertTrue(ok)
        self.assertEqual(level, "ok")

    def test_block_shell_injection(self):
        ok, level, msg = validate_console_line("cli", "--file a.csv; rm -rf /")
        self.assertFalse(ok)
        self.assertIn("禁止", msg)

    def test_warn_clean(self):
        ok, level, _ = validate_console_line("cli", "--clean reports")
        self.assertTrue(ok)
        self.assertEqual(level, "warn")

    def test_chat_allowed_command(self):
        ok, level, _ = validate_console_line("chat", "doc api_docs/apispec_1.json generate")
        self.assertTrue(ok)

    def test_chat_rejects_unknown(self):
        ok, level, msg = validate_console_line("chat", "shell whoami")
        self.assertFalse(ok)
        self.assertIn("不允许", msg)

    def test_build_main_command_cli(self):
        cmd = build_main_command("python", "main.py", "cli", "--help")
        self.assertEqual(cmd, ["python", "main.py", "--help"])

    def test_build_help_command_chat(self):
        cmd = build_help_command("python", "main.py", "chat")
        self.assertEqual(cmd[-2:], ["--chat", "help"])


if __name__ == "__main__":
    unittest.main()
