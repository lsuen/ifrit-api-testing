#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：日志与报告保留策略、CLI 清理
"""
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from config.config import Config
from core.run_artifacts import get_runs_root


DATE_IN_NAME = re.compile(r"(\d{8})")


@dataclass
class CleanResult:
    """清理结果摘要。"""

    target: str
    removed: List[str] = field(default_factory=list)
    kept: int = 0
    dry_run: bool = False

    @property
    def removed_count(self) -> int:
        return len(self.removed)


def _parse_date_from_name(name: str) -> Optional[datetime]:
    match = DATE_IN_NAME.search(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d")
    except ValueError:
        return None


def _is_older_than(path: str, keep_days: int, now: Optional[datetime] = None) -> bool:
    if keep_days <= 0:
        return False
    current = now or datetime.now()
    cutoff = current - timedelta(days=keep_days)

    parsed = _parse_date_from_name(os.path.basename(path))
    if parsed:
        return parsed.date() < cutoff.date()

    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    return mtime < cutoff


def clean_logs(
    keep_days: Optional[int] = None,
    dry_run: bool = False,
    config: Optional[Config] = None,
) -> CleanResult:
    """清理 logs/daily 与 logs/errors 中过期文件。"""
    cfg = config or Config()
    retention = cfg.get_retention_config()
    days = keep_days if keep_days is not None else retention["logs_keep_days"]
    result = CleanResult(target="logs", dry_run=dry_run)

    targets = [
        os.path.join(cfg.logs_dir, "daily"),
        os.path.join(cfg.logs_dir, "errors"),
        os.path.join(cfg.logs_dir, "runs"),
    ]
    legacy_main = os.path.join(cfg.logs_dir, "api_automation.log")
    if os.path.isfile(legacy_main) and _is_older_than(legacy_main, days):
        if dry_run:
            result.removed.append(legacy_main)
        else:
            os.remove(legacy_main)
            result.removed.append(legacy_main)

    for directory in targets:
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if not _is_older_than(path, days):
                result.kept += 1
                continue
            if dry_run:
                result.removed.append(path)
            else:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
                result.removed.append(path)

    return result


def clean_reports(
    keep_days: Optional[int] = None,
    keep_last: Optional[int] = None,
    dry_run: bool = False,
    config: Optional[Config] = None,
) -> CleanResult:
    """清理 reports/runs 中过期或超出保留数量的 run。"""
    cfg = config or Config()
    retention = cfg.get_retention_config()
    days = keep_days if keep_days is not None else retention["reports_keep_days"]
    last_n = keep_last if keep_last is not None else retention["reports_keep_last"]
    result = CleanResult(target="reports", dry_run=dry_run)

    runs_root = get_runs_root(cfg)
    if not os.path.isdir(runs_root):
        return result

    run_dirs = sorted(
        [
            os.path.join(runs_root, name)
            for name in os.listdir(runs_root)
            if os.path.isdir(os.path.join(runs_root, name))
        ],
        reverse=True,
    )

    for index, path in enumerate(run_dirs):
        too_old = _is_older_than(path, days)
        over_count = last_n > 0 and index >= last_n
        if not too_old and not over_count:
            result.kept += 1
            continue
        if dry_run:
            result.removed.append(path)
        else:
            shutil.rmtree(path, ignore_errors=True)
            result.removed.append(path)

    _sync_latest_pointer(cfg, dry_run=dry_run)
    return result


def _sync_latest_pointer(cfg: Config, dry_run: bool = False) -> None:
    from core.run_artifacts import LATEST_RUN_FILE, get_latest_run_id

    runs_root = get_runs_root(cfg)
    if not os.path.isdir(runs_root):
        return
    remaining = sorted(
        [name for name in os.listdir(runs_root) if os.path.isdir(os.path.join(runs_root, name))],
        reverse=True,
    )
    latest_path = os.path.join(cfg.reports_dir, LATEST_RUN_FILE)
    if not remaining:
        if os.path.isfile(latest_path) and not dry_run:
            os.remove(latest_path)
        return
    current = get_latest_run_id(cfg)
    if current in remaining:
        return
    if dry_run:
        return
    with open(latest_path, "w", encoding="utf-8") as handle:
        handle.write(remaining[0])


def clean_all(
    keep_days: Optional[int] = None,
    keep_last: Optional[int] = None,
    dry_run: bool = False,
    config: Optional[Config] = None,
) -> List[CleanResult]:
    """清理日志 + 报告。"""
    return [
        clean_logs(keep_days=keep_days, dry_run=dry_run, config=config),
        clean_reports(keep_days=keep_days, keep_last=keep_last, dry_run=dry_run, config=config),
    ]


def maybe_auto_clean_before_run(config: Optional[Config] = None) -> None:
    """若配置启用，在测试前自动清理。"""
    cfg = config or Config()
    retention = cfg.get_retention_config()
    if not retention.get("auto_clean_before_run"):
        return
    clean_all(
        keep_days=None,
        keep_last=retention.get("reports_keep_last"),
        dry_run=False,
        config=cfg,
    )


def format_clean_summary(results: List[CleanResult]) -> str:
    """生成 CLI 友好的清理摘要。"""
    lines = ["[IFRIT] ── 清理结果 ──"]
    for item in results:
        action = "将删除" if item.dry_run else "已删除"
        lines.append(
            f"[IFRIT] {item.target}: {action} {item.removed_count} 项, 保留 {item.kept} 项"
        )
        preview = item.removed[:5]
        for path in preview:
            lines.append(f"[IFRIT]   - {path}")
        if item.removed_count > len(preview):
            lines.append(f"[IFRIT]   ... 另有 {item.removed_count - len(preview)} 项")
    return "\n".join(lines)
