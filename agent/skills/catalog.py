#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 目录扫描与元数据。"""
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.skills.paths import SkillStorePaths
from agent.skills.repos import SkillRepo, load_repos
from agent.skills.skill_md import make_skill_id, parse_skill_md


@dataclass
class SkillCatalogItem:
  id: str
  name: str
  description: Optional[str]
  repo_id: str
  repo_label: str
  relative_path: str
  staged: bool = False
  enabled: bool = False
  source: str = "remote"  # remote | custom | builtin

  def to_dict(self) -> Dict[str, Any]:
    return asdict(self)


def _load_staged_meta(paths: SkillStorePaths) -> Dict[str, Any]:
  if not paths.staged_meta.is_file():
    return {"skills": {}}
  try:
    with open(paths.staged_meta, "r", encoding="utf-8") as handle:
      data = json.load(handle)
    return data if isinstance(data, dict) else {"skills": {}}
  except (json.JSONDecodeError, OSError):
    return {"skills": {}}


def save_staged_meta(paths: SkillStorePaths, meta: Dict[str, Any]) -> None:
  paths.ensure_dirs()
  with open(paths.staged_meta, "w", encoding="utf-8") as handle:
    json.dump(meta, handle, ensure_ascii=False, indent=2)


def _scan_repo_dir(
  root: Path,
  current: Path,
  repo: SkillRepo,
  staged: Dict[str, Any],
  out: List[SkillCatalogItem],
) -> None:
  try:
    entries = list(current.iterdir())
  except OSError:
    return
  for entry in entries:
    if entry.name == ".git":
      continue
    if not entry.is_dir():
      continue
    skill_md = entry / "SKILL.md"
    if skill_md.is_file():
      relative = entry.relative_to(root).as_posix()
      skill_id = make_skill_id(repo.id, relative)
      try:
        name, description = parse_skill_md(skill_md)
      except OSError:
        name, description = entry.name, None
      record = staged.get("skills", {}).get(skill_id, {})
      out.append(
        SkillCatalogItem(
          id=skill_id,
          name=name,
          description=description,
          repo_id=repo.id,
          repo_label=repo.label(),
          relative_path=relative,
          staged=bool(record),
          enabled=bool(record.get("enabled")),
          source="remote",
        )
      )
    else:
      _scan_repo_dir(root, entry, repo, staged, out)


def build_catalog(paths: SkillStorePaths, query: str = "") -> List[SkillCatalogItem]:
  repos = load_repos(paths)
  staged = _load_staged_meta(paths)
  items: List[SkillCatalogItem] = []
  q = query.strip().lower()

  for repo in repos:
    if not repo.enabled:
      continue
    repo_dir = paths.repo_cache_dir(repo.id)
    if not repo_dir.is_dir():
      continue
    _scan_repo_dir(repo_dir, repo_dir, repo, staged, items)

  # 已安装但 cache 里没有的也列出
  for skill_id, record in staged.get("skills", {}).items():
    if any(i.id == skill_id for i in items):
      continue
    items.append(
      SkillCatalogItem(
        id=skill_id,
        name=record.get("name", skill_id),
        description=record.get("description"),
        repo_id=record.get("repo_id", ""),
        repo_label=record.get("repo_id", ""),
        relative_path=record.get("relative_path", ""),
        staged=True,
        enabled=bool(record.get("enabled")),
        source="remote",
      )
    )

  if q:
    items = [
      i
      for i in items
      if q in i.name.lower()
      or q in i.id.lower()
      or (i.description and q in i.description.lower())
      or q in i.repo_label.lower()
    ]
  items.sort(key=lambda x: x.name.lower())
  return items


def install_skill(paths: SkillStorePaths, skill_id: str) -> Path:
  """从 cache 复制到 library 并写入 staged 元数据。"""
  staged = _load_staged_meta(paths)
  catalog = build_catalog(paths)
  item = next((i for i in catalog if i.id == skill_id), None)
  if not item:
    raise ValueError(f"未找到技能: {skill_id}")

  source = paths.repo_cache_dir(item.repo_id) / item.relative_path.replace("/", "\\")
  if not source.is_dir():
    source = paths.repo_cache_dir(item.repo_id) / item.relative_path
  if not source.is_dir():
    raise FileNotFoundError("技能源目录不存在，请先刷新仓库")

  dest = paths.library_skill_dir(skill_id)
  if dest.is_dir():
    shutil.rmtree(dest)
  shutil.copytree(source, dest)

  staged.setdefault("skills", {})[skill_id] = {
    "name": item.name,
    "description": item.description,
    "repo_id": item.repo_id,
    "relative_path": item.relative_path,
    "installed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "enabled": staged.get("skills", {}).get(skill_id, {}).get("enabled", False),
  }
  save_staged_meta(paths, staged)
  return dest


def uninstall_skill(paths: SkillStorePaths, skill_id: str) -> None:
  staged = _load_staged_meta(paths)
  staged.get("skills", {}).pop(skill_id, None)
  save_staged_meta(paths, staged)
  lib = paths.library_skill_dir(skill_id)
  if lib.is_dir():
    shutil.rmtree(lib, ignore_errors=True)


def set_skill_enabled(paths: SkillStorePaths, skill_id: str, enabled: bool) -> None:
  staged = _load_staged_meta(paths)
  record = staged.get("skills", {}).get(skill_id)
  if not record:
    raise ValueError(f"技能未安装: {skill_id}")
  record["enabled"] = enabled
  save_staged_meta(paths, staged)


def read_skill_content(paths: SkillStorePaths, skill_id: str) -> Dict[str, Any]:
  lib = paths.library_skill_dir(skill_id)
  skill_md = lib / "SKILL.md"
  if not skill_md.is_file():
    cache_item = next((i for i in build_catalog(paths) if i.id == skill_id), None)
    if cache_item:
      src = paths.repo_cache_dir(cache_item.repo_id) / cache_item.relative_path / "SKILL.md"
      if src.is_file():
        return {
          "path": str(src),
          "content": src.read_text(encoding="utf-8", errors="replace"),
          "readonly": True,
        }
    raise FileNotFoundError(f"SKILL.md 不存在: {skill_id}")
  return {
    "path": str(skill_md),
    "content": skill_md.read_text(encoding="utf-8", errors="replace"),
    "readonly": False,
  }


def save_skill_content(paths: SkillStorePaths, skill_id: str, content: str) -> None:
  lib = paths.library_skill_dir(skill_id)
  if not lib.is_dir():
    raise FileNotFoundError(f"请先安装技能: {skill_id}")
  skill_md = lib / "SKILL.md"
  skill_md.write_text(content, encoding="utf-8")
  try:
    name, description = parse_skill_md(skill_md)
    staged = _load_staged_meta(paths)
    if skill_id in staged.get("skills", {}):
      staged["skills"][skill_id]["name"] = name
      staged["skills"][skill_id]["description"] = description
      save_staged_meta(paths, staged)
  except OSError:
    pass
