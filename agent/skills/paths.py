#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 商店路径约定（参考 sugt store 布局，落在项目 .ifrit/skills）。"""
from pathlib import Path
from typing import Optional

from config.loader import get_project_root


class SkillStorePaths:
  def __init__(self, project_root: Optional[str] = None):
    root = Path(project_root or get_project_root())
    self.root = root
    self.store_dir = root / ".ifrit" / "skills"
    self.repos_file = self.store_dir / "repos.yaml"
    self.staged_meta = self.store_dir / "staged.json"
    self.cache_dir = self.store_dir / "cache"
    self.library_dir = self.store_dir / "library"
    self.custom_dir = root / "agent" / "skills" / "custom"

  def ensure_dirs(self) -> None:
    self.store_dir.mkdir(parents=True, exist_ok=True)
    self.cache_dir.mkdir(parents=True, exist_ok=True)
    self.library_dir.mkdir(parents=True, exist_ok=True)
    self.custom_dir.mkdir(parents=True, exist_ok=True)

  def repo_cache_dir(self, repo_id: str) -> Path:
    return self.cache_dir / repo_id

  def library_skill_dir(self, skill_id: str) -> Path:
    return self.library_dir / skill_id
