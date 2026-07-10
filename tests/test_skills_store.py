#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill MD 解析与商店路径测试。"""
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.skills.skill_md import make_skill_id, parse_skill_md
from agent.skills.repos import parse_repo_url
from agent.skills.registry import list_skills_detail, get_skill_detail


class TestSkillMd(unittest.TestCase):
    def test_parse_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("---\nname: Demo\ndescription: Hello\n---\n", encoding="utf-8")
            name, desc = parse_skill_md(path)
            self.assertEqual(name, "Demo")
            self.assertEqual(desc, "Hello")

    def test_make_skill_id(self):
        sid = make_skill_id("repo-a", "foo/bar")
        self.assertIn("repo-a", sid)
        self.assertIn("foo--bar", sid)

    def test_parse_github_url(self):
        repo = parse_repo_url("https://github.com/jeffallan/claude-skills")
        self.assertEqual(repo.host, "github")
        self.assertEqual(repo.owner, "jeffallan")

    def test_parse_gitee_url(self):
        repo = parse_repo_url("https://gitee.com/hongmaple/agent-academy")
        self.assertEqual(repo.host, "gitee")
        self.assertEqual(repo.owner, "hongmaple")

    def test_builtin_detail(self):
        detail = get_skill_detail("case_generation")
        self.assertEqual(detail["name"], "case_generation")
        self.assertTrue(len(detail["actions"]) >= 3)

    def test_list_skills_detail(self):
        items = list_skills_detail()
        self.assertTrue(any(i["name"] == "ai_quality_loop" for i in items))


if __name__ == "__main__":
    unittest.main()
