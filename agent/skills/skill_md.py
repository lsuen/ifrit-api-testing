#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SKILL.md 轻量解析（对齐 sugt catalog::parse_skill_md）。"""
from pathlib import Path
from typing import Optional, Tuple


def parse_skill_md(path: Path) -> Tuple[str, Optional[str]]:
  raw = path.read_text(encoding="utf-8", errors="replace")
  name: Optional[str] = None
  description: Optional[str] = None

  if raw.startswith("---"):
    end = raw[3:].find("---")
    if end >= 0:
      front = raw[3 : 3 + end]
      for line in front.splitlines():
        line = line.strip()
        if ":" not in line:
          continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip().strip('"').strip("'")
        if key == "name" and value:
          name = value
        if key == "description" and value:
          description = value

  if not name:
    for line in raw.splitlines():
      trimmed = line.strip()
      if trimmed.startswith("# "):
        name = trimmed[2:].strip()
        break

  if not description:
    after_heading = False
    for line in raw.splitlines():
      trimmed = line.strip()
      if trimmed.startswith("# "):
        after_heading = True
        continue
      if after_heading and trimmed and not trimmed.startswith("#"):
        description = trimmed
        break

  fallback = path.parent.name or "skill"
  return name or fallback, description


def make_skill_id(repo_id: str, relative_path: str) -> str:
  slug = relative_path.replace("/", "--").replace("\\", "--").replace(" ", "-")
  return f"{repo_id}__{slug}"
