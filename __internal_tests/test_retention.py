#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""run_artifacts 与 retention 单元测试。"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from core.retention import clean_logs, clean_reports
from core.run_artifacts import (
    create_run_directory,
    get_latest_run_id,
    get_latest_run_paths,
)


class TestRunArtifacts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cfg = Config()
        self.cfg.base_dir = self.temp_dir
        self.cfg.reports_dir = os.path.join(self.temp_dir, "reports")
        self.cfg.logs_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.cfg.reports_dir, exist_ok=True)

    def test_create_and_resolve_latest_run(self):
        paths = create_run_directory(config=self.cfg, suite="smoke", test_type="csv")
        self.assertTrue(os.path.isdir(paths["allure_dir"]))
        self.assertEqual(get_latest_run_id(self.cfg), paths["run_id"])
        latest = get_latest_run_paths(self.cfg)
        self.assertEqual(latest["run_id"], paths["run_id"])


class TestRetention(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cfg = Config()
        self.cfg.base_dir = self.temp_dir
        self.cfg.reports_dir = os.path.join(self.temp_dir, "reports")
        self.cfg.logs_dir = os.path.join(self.temp_dir, "logs")
        daily_dir = os.path.join(self.cfg.logs_dir, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        old_day = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        self.old_log = os.path.join(daily_dir, f"daily_{old_day}.log")
        with open(self.old_log, "w", encoding="utf-8") as handle:
            handle.write("old")

    def test_clean_logs_removes_old_files(self):
        result = clean_logs(keep_days=7, dry_run=False, config=self.cfg)
        self.assertIn(self.old_log, result.removed)
        self.assertFalse(os.path.exists(self.old_log))

    def test_clean_reports_respects_keep_last(self):
        runs_root = os.path.join(self.cfg.reports_dir, "runs")
        os.makedirs(runs_root, exist_ok=True)
        for name in ("20260101_120000", "20260102_120000", "20260103_120000"):
            os.makedirs(os.path.join(runs_root, name), exist_ok=True)
        result = clean_reports(keep_days=0, keep_last=2, dry_run=False, config=self.cfg)
        remaining = sorted(os.listdir(runs_root))
        self.assertEqual(len(remaining), 2)
        self.assertEqual(get_latest_run_id(self.cfg), "20260103_120000")


if __name__ == "__main__":
    unittest.main(verbosity=2)
