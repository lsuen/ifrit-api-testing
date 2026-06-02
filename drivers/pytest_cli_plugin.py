#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：pytest CLI 精简输出插件（每条 PASS/FAIL + 不写冗长 IO）
"""
import os
import re


def _extract_case_label(nodeid: str) -> str:
    """从 nodeid 提取可读用例名。"""
    match = re.search(r"\[(.+?)\]", nodeid)
    if match:
        return match.group(1)
    return nodeid.split("::")[-1]


def pytest_configure(config):
    if os.getenv("IFRIT_CLI_MODE") == "1":
        config.option.tbstyle = "line"
        config.option.verbose = 0


def pytest_runtest_logreport(report):
    if os.getenv("IFRIT_CLI_MODE") != "1":
        return
    if report.when != "call":
        return

    label = _extract_case_label(report.nodeid)
    if report.passed:
        print(f"\n[IFRIT] PASS {label}", flush=True)
    elif report.failed:
        reason = ""
        if report.longrepr:
            text = str(report.longrepr)
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("E ") or "AssertionError" in line or "Failed:" in line:
                    reason = line[:120]
                    break
        suffix = f" | {reason}" if reason else ""
        print(f"\n[IFRIT] FAIL {label}{suffix}", flush=True)
    elif report.skipped:
        print(f"\n[IFRIT] SKIP {label}", flush=True)
