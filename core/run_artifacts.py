#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：单次测试运行的日志/报告目录管理
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional

from config.config import Config

LATEST_RUN_FILE = "latest.txt"


def create_run_id() -> str:
    """生成 run 目录名：YYYYMMDD_HHMMSS。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_runs_root(config: Optional[Config] = None) -> str:
    cfg = config or Config()
    return os.path.join(cfg.reports_dir, "runs")


def create_run_directory(
    config: Optional[Config] = None,
    suite: Optional[str] = None,
    test_type: Optional[str] = None,
) -> Dict[str, str]:
    """创建本次运行的报告目录并更新 latest 指针。"""
    cfg = config or Config()
    run_id = create_run_id()
    run_dir = os.path.join(get_runs_root(cfg), run_id)
    allure_dir = os.path.join(run_dir, "allure-results")
    html_dir = os.path.join(run_dir, "html")
    os.makedirs(allure_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    meta = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "suite": suite or "",
        "test_type": test_type or "",
    }
    with open(os.path.join(run_dir, "meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)

    latest_path = os.path.join(cfg.reports_dir, LATEST_RUN_FILE)
    with open(latest_path, "w", encoding="utf-8") as handle:
        handle.write(run_id)

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "allure_dir": allure_dir,
        "html_dir": html_dir,
    }


def get_latest_run_id(config: Optional[Config] = None) -> Optional[str]:
    cfg = config or Config()
    latest_path = os.path.join(cfg.reports_dir, LATEST_RUN_FILE)
    if not os.path.isfile(latest_path):
        return None
    with open(latest_path, "r", encoding="utf-8") as handle:
        run_id = handle.read().strip()
    return run_id or None


def get_latest_run_paths(config: Optional[Config] = None) -> Optional[Dict[str, str]]:
    """读取 latest 对应的 run 路径。"""
    cfg = config or Config()
    run_id = get_latest_run_id(cfg)
    if not run_id:
        return None
    run_dir = os.path.join(get_runs_root(cfg), run_id)
    if not os.path.isdir(run_dir):
        return None
    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "allure_dir": os.path.join(run_dir, "allure-results"),
        "html_dir": os.path.join(run_dir, "html"),
    }


def get_latest_html_index(config: Optional[Config] = None) -> Optional[str]:
    """返回相对项目根的最新 HTML 报告 index 路径。"""
    paths = get_latest_run_paths(config)
    if not paths:
        return None
    index_path = os.path.join(paths["html_dir"], "index.html")
    if not os.path.isfile(index_path):
        return None
    cfg = config or Config()
    return os.path.relpath(index_path, cfg.base_dir).replace("\\", "/")


def legacy_allure_dir(config: Optional[Config] = None) -> str:
    """兼容旧路径 reports/allure_reports（不存在则回退 latest）。"""
    paths = get_latest_run_paths(config)
    if paths and os.path.isdir(paths["allure_dir"]):
        return paths["allure_dir"]
    cfg = config or Config()
    return os.path.join(cfg.reports_dir, "allure_reports")
