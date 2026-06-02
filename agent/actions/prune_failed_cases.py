#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：运行用例后删除 CSV 中失败项，保障 AI 用例目录质量
创建时间：2026-06-02
"""
import csv
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Set

from agent.actions.base import Action

logger = logging.getLogger(__name__)


class PruneFailedCasesAction(Action):
    """删除测试失败对应的 CSV 行。"""

    name = "prune_failed_cases"
    description = "执行 pytest 后从 CSV 中移除失败用例行"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        csv_path = context.get("csv_path") or context.get("output_path")
        if not csv_path or not os.path.isfile(csv_path):
            logger.warning("未指定有效 CSV，跳过 prune")
            context["pruned_count"] = 0
            return context

        env_names = context.get("env_names") or ["environment"]
        exit_code, failed_ids = self._run_pytest_and_collect_failures(csv_path, env_names)

        if not failed_ids:
            context["pruned_count"] = 0
            context["test_exit_code"] = exit_code
            logger.info("无失败用例，无需 prune")
            return context

        removed = self._remove_rows_by_id(csv_path, failed_ids)
        context["pruned_count"] = removed
        context["failed_ids"] = list(failed_ids)
        context["test_exit_code"] = exit_code
        logger.info("已从 %s 删除 %s 条失败用例", csv_path, removed)
        return context

    def _run_pytest_and_collect_failures(
        self, csv_path: str, env_names: List[str]
    ) -> tuple:
        """运行 pytest 并解析失败用例 id。"""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "drivers/test_api_csv_driver.py",
            "-v",
            "--tb=no",
            "-q",
            "--test-data-file",
            csv_path,
        ]
        for env_name in env_names:
            cmd.extend(["--env", env_name])

        logger.info("执行验证: %s", " ".join(cmd))
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = completed.stdout + completed.stderr
        failed_ids = self._parse_failed_case_ids(output)
        return completed.returncode, failed_ids

    @staticmethod
    def _parse_failed_case_ids(pytest_output: str) -> Set[str]:
        """从 pytest 输出解析失败用例 id（格式: case_id - case_name）。"""
        failed_ids: Set[str] = set()
        for line in pytest_output.splitlines():
            line = line.strip()
            if "FAILED" not in line:
                continue
            match_part = line.split("FAILED")[-1].strip()
            if "::" in match_part:
                param = match_part.split("[")[-1].rstrip("]")
                case_id = param.split(" - ")[0].strip()
                if case_id:
                    failed_ids.add(case_id)
        return failed_ids

    @staticmethod
    def _remove_rows_by_id(csv_path: str, failed_ids: Set[str]) -> int:
        """从 CSV 删除指定 id 的行。"""
        with open(csv_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or []
            rows = list(reader)

        if not fieldnames:
            return 0

        id_column = "id" if "id" in fieldnames else "case_id"
        kept = []
        removed = 0
        for row in rows:
            row_id = str(row.get(id_column, row.get("case_id", ""))).strip()
            if row_id in failed_ids:
                removed += 1
            else:
                kept.append(row)

        if removed == 0:
            return 0

        with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept)
        return removed
