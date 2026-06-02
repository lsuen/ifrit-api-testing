#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告管理器
负责生成和展示测试报告
"""

import os
import platform
import subprocess
import logging

from core.run_artifacts import get_latest_html_index, get_latest_run_paths


class ReportManager:
    """报告管理器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _resolve_dirs(self, allure_dir=None, html_dir=None):
        if allure_dir and html_dir:
            return allure_dir, html_dir
        paths = get_latest_run_paths()
        if paths:
            return paths["allure_dir"], paths["html_dir"]
        return "./reports/allure_reports", "./reports/html"

    def serve_report(self, allure_dir=None):
        """启动 Allure 报告服务器。"""
        try:
            resolved_allure, _ = self._resolve_dirs(allure_dir=allure_dir, html_dir=None)
            if not os.path.exists(resolved_allure):
                self.logger.error("Allure 结果目录不存在: %s", resolved_allure)
                return

            if not os.listdir(resolved_allure):
                self.logger.warning("Allure 结果目录为空，没有可显示的报告")
                return

            self.logger.info("启动 Allure 报告服务器")
            cmd = ["allure", "serve", resolved_allure]
            self.logger.info("执行命令: %s", " ".join(cmd))
            if platform.system().lower() == "windows":
                subprocess.run(cmd, shell=True)
            else:
                subprocess.run(cmd)
        except FileNotFoundError:
            self.logger.error("未找到 allure 命令，请确保已安装 Allure 命令行工具")
        except Exception as error:
            self.logger.error("启动 Allure 报告服务器时发生异常: %s", error)

    def generate_html_report(self, allure_dir=None, html_dir=None):
        """生成 HTML 格式的 Allure 报告。"""
        try:
            resolved_allure, resolved_html = self._resolve_dirs(allure_dir, html_dir)
            os.makedirs(resolved_html, exist_ok=True)

            if not os.path.exists(resolved_allure):
                self.logger.error("Allure 结果目录不存在: %s", resolved_allure)
                return False

            if not os.listdir(resolved_allure):
                self.logger.warning("Allure 结果目录为空，没有可生成的报告")
                return False

            self.logger.info("生成 HTML 格式的 Allure 报告")
            cmd = [
                "allure",
                "generate",
                resolved_allure,
                "-o",
                resolved_html,
                "--clean",
            ]
            self.logger.info("执行命令: %s", " ".join(cmd))
            env = dict(os.environ, LANG="zh_CN.UTF-8", LC_ALL="zh_CN.UTF-8")
            if platform.system().lower() == "windows":
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode != 0:
                self.logger.error("HTML 报告生成失败: %s", result.stderr)
                return False

            self.logger.info("HTML 报告生成成功，路径: %s", resolved_html)
            self._log_history_stats(resolved_html)
            return True
        except FileNotFoundError:
            self.logger.error("未找到 allure 命令，请确保已安装 Allure 命令行工具")
            return False
        except Exception as error:
            self.logger.error("生成 HTML 报告时发生异常: %s", error)
            return False

    @staticmethod
    def _log_history_stats(html_dir: str) -> None:
        logger = logging.getLogger(__name__)
        summary_file = os.path.join(html_dir, "history", "history-trend.json")
        if not os.path.exists(summary_file):
            logger.warning("测试统计数据文件不存在")
            return
        try:
            import json

            with open(summary_file, "r", encoding="utf-8") as handle:
                history_data = json.load(handle)
            if history_data and isinstance(history_data, list) and history_data:
                latest = history_data[-1]["data"]
                logger.info(
                    "总计执行用例数: %s, 通过: %s, 失败: %s, 跳过: %s, 错误: %s",
                    latest.get("total", 0),
                    latest.get("passed", 0),
                    latest.get("failed", 0),
                    latest.get("skipped", 0),
                    latest.get("broken", 0),
                )
        except Exception as error:
            logger.error("读取测试统计数据时发生异常: %s", error)

    @staticmethod
    def latest_report_path() -> str:
        """返回最新 HTML 报告 index 的相对路径。"""
        path = get_latest_html_index()
        return path or "reports/latest.txt"
