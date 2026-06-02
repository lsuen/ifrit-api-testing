#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Allure environment.properties 写入。"""
import os
import subprocess
from typing import List, Optional

from config.config import Config


def write_allure_environment(
    allure_dir: str,
    env_names: Optional[List[str]] = None,
    suite: Optional[str] = None,
    test_path: Optional[str] = None,
    test_type: Optional[str] = None,
) -> None:
    """写入 Allure 环境信息，便于报告追溯。"""
    if not allure_dir:
        return

    os.makedirs(allure_dir, exist_ok=True)
    config = Config(env_names=env_names)

    git_commit = "unknown"
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            git_commit = completed.stdout.strip()
    except OSError:
        pass

    lines = [
        f"Base.URL={config.get_base_url()}",
        f"Environment={','.join(env_names) if env_names else 'environment'}",
        f"Suite={suite or 'manual'}",
        f"TestType={test_type or 'auto'}",
        f"TestFile={test_path or 'directory'}",
        f"Git.Commit={git_commit}",
    ]

    env_file = os.path.join(allure_dir, "environment.properties")
    with open(env_file, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
