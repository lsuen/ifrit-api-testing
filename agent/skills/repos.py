#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Skill 远程仓库管理（GitHub / Gitee 浅克隆）。"""
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml

from agent.skills.paths import SkillStorePaths

REPO_URL_RE = re.compile(
  r"^https?://(?P<host>gitee\.com|github\.com)/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
  re.I,
)


@dataclass
class SkillRepo:
  id: str
  host: str
  owner: str
  repo: str
  branch: str = "main"
  enabled: bool = True
  last_refresh_at: Optional[str] = None
  last_error: Optional[str] = None

  def label(self) -> str:
    return f"{self.owner}/{self.repo}"

  def clone_url(self) -> str:
    if self.host == "gitee":
      return f"https://gitee.com/{self.owner}/{self.repo}.git"
    return f"https://github.com/{self.owner}/{self.repo}.git"


def parse_repo_url(url: str, branch: str = "main") -> SkillRepo:
  match = REPO_URL_RE.match(url.strip())
  if not match:
    raise ValueError(f"不支持的仓库 URL: {url}")
  host_raw = match.group("host").lower()
  host = "gitee" if "gitee" in host_raw else "github"
  owner = match.group("owner")
  repo = match.group("repo")
  repo_id = f"{owner}-{repo}".lower().replace("_", "-")
  return SkillRepo(id=repo_id, host=host, owner=owner, repo=repo, branch=branch)


def _repo_from_dict(data: Dict[str, Any]) -> SkillRepo:
  return SkillRepo(
    id=str(data["id"]),
    host=str(data.get("host", "github")),
    owner=str(data["owner"]),
    repo=str(data["repo"]),
    branch=str(data.get("branch", "main")),
    enabled=bool(data.get("enabled", True)),
    last_refresh_at=data.get("last_refresh_at"),
    last_error=data.get("last_error"),
  )


def _repo_to_dict(repo: SkillRepo) -> Dict[str, Any]:
  return {
    "id": repo.id,
    "host": repo.host,
    "owner": repo.owner,
    "repo": repo.repo,
    "branch": repo.branch,
    "enabled": repo.enabled,
    "last_refresh_at": repo.last_refresh_at,
    "last_error": repo.last_error,
  }


def _default_repos_path() -> Path:
  return Path(__file__).resolve().parents[2] / "config" / "skills" / "repos.default.yaml"


def load_repos(paths: SkillStorePaths) -> List[SkillRepo]:
  paths.ensure_dirs()
  if not paths.repos_file.is_file():
    default = _default_repos_path()
    if default.is_file():
      shutil.copy(default, paths.repos_file)
  if not paths.repos_file.is_file():
    return []
  with open(paths.repos_file, "r", encoding="utf-8") as handle:
    data = yaml.safe_load(handle) or {}
  repos = data.get("repos") or []
  return [_repo_from_dict(item) for item in repos if isinstance(item, dict)]


def save_repos(paths: SkillStorePaths, repos: List[SkillRepo]) -> None:
  paths.ensure_dirs()
  payload = {"repos": [_repo_to_dict(r) for r in repos]}
  with open(paths.repos_file, "w", encoding="utf-8") as handle:
    yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)


def add_repo(paths: SkillStorePaths, url: str, branch: str = "main") -> SkillRepo:
  repos = load_repos(paths)
  new_repo = parse_repo_url(url, branch)
  for existing in repos:
    if existing.id == new_repo.id:
      raise ValueError(f"仓库已存在: {existing.label()}")
  repos.append(new_repo)
  save_repos(paths, repos)
  return new_repo


def remove_repo(paths: SkillStorePaths, repo_id: str) -> bool:
  repos = load_repos(paths)
  kept = [r for r in repos if r.id != repo_id]
  if len(kept) == len(repos):
    return False
  cache = paths.repo_cache_dir(repo_id)
  if cache.is_dir():
    shutil.rmtree(cache, ignore_errors=True)
  save_repos(paths, kept)
  return True


def refresh_repo(paths: SkillStorePaths, repo: SkillRepo, log=None) -> Tuple[bool, str]:
  """浅克隆仓库到 cache。log 回调用于流式输出。"""
  def emit(msg: str) -> None:
    if log:
      log(msg)
    else:
      print(msg, flush=True)

  dest = paths.repo_cache_dir(repo.id)
  if dest.is_dir():
    shutil.rmtree(dest, ignore_errors=True)
  dest.parent.mkdir(parents=True, exist_ok=True)

  clone_url = repo.clone_url()
  emit(f"[IFRIT] SKILL_REPO clone start id={repo.id} url={clone_url} branch={repo.branch}")
  cmd = [
    "git",
    "clone",
    "--depth",
    "1",
    "--branch",
    repo.branch,
    clone_url,
    str(dest),
  ]
  try:
    proc = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      encoding="utf-8",
      errors="replace",
      timeout=300,
    )
  except subprocess.TimeoutExpired:
    repo.last_error = "git clone 超时"
    emit(f"[IFRIT] SKILL_REPO clone failed id={repo.id} error=timeout")
    return False, repo.last_error
  except FileNotFoundError:
    repo.last_error = "未找到 git 命令，请安装 Git"
    emit(f"[IFRIT] SKILL_REPO clone failed id={repo.id} error=no_git")
    return False, repo.last_error

  if proc.returncode != 0:
    err = (proc.stderr or proc.stdout or "unknown").strip()[:500]
    repo.last_error = err
    emit(f"[IFRIT] SKILL_REPO clone failed id={repo.id} error={err}")
    return False, err

  repo.last_refresh_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  repo.last_error = None
  emit(f"[IFRIT] SKILL_REPO clone ok id={repo.id} path={dest.as_posix()}")
  return True, ""


def refresh_all(paths: SkillStorePaths, log=None) -> Dict[str, Any]:
  repos = load_repos(paths)
  results = {"ok": 0, "failed": 0, "repos": []}
  for repo in repos:
    if not repo.enabled:
      continue
    ok, err = refresh_repo(paths, repo, log=log)
    if ok:
      results["ok"] += 1
    else:
      results["failed"] += 1
    results["repos"].append({"id": repo.id, "ok": ok, "error": err or None})
  save_repos(paths, repos)
  return results
