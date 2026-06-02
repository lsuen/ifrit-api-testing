#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：统一测试用例发现与加载（CSV / Excel / JSON，manual / ai / smoke）
创建时间：2026-06-02
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config.config import Config
from utils.test_case_reader import DataHandler

logger = logging.getLogger(__name__)

FORMAT_CSV = "csv"
FORMAT_EXCEL = "excel"
FORMAT_JSON = "json"
FORMAT_ALL = "all"

_FORMAT_EXTENSIONS = {
    FORMAT_CSV: (".csv",),
    FORMAT_EXCEL: (".xlsx", ".xls"),
    FORMAT_JSON: (".json",),
}


@dataclass
class FileDiscovery:
    """单个用例文件的发现结果。"""

    path: str
    case_count: int
    data_format: str
    exists: bool = True


@dataclass
class DiscoveryResult:
    """用例发现与加载结果。"""

    suite: str
    data_format: str
    scan_dirs: List[str] = field(default_factory=list)
    single_file: str = ""
    files: List[FileDiscovery] = field(default_factory=list)
    cases: List[dict] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_cases(self) -> int:
        return len(self.cases)

    @property
    def is_empty(self) -> bool:
        return self.total_cases == 0


def infer_suite_from_path(file_path: str) -> str:
    """从文件路径推断套件。"""
    normalized = file_path.replace("\\", "/").lower()
    if "/fixtures/ai/" in normalized or "/ai/csv/" in normalized:
        return Config.SUITE_AI
    if "/fixtures/smoke/" in normalized or "/smoke/csv/" in normalized:
        return Config.SUITE_SMOKE
    return Config.SUITE_MANUAL


def resolve_suite(
    suite: Optional[str],
    single_file: Optional[str] = None,
) -> str:
    """解析最终套件名称。"""
    if suite:
        return suite
    if single_file:
        return infer_suite_from_path(single_file)
    return Config.SUITE_MANUAL


def get_scan_dirs(config: Config, data_format: str, suite: str) -> List[str]:
    """获取指定格式与套件下的扫描目录列表。"""
    suites = list(Config.ALL_SUITES) if suite == Config.SUITE_ALL else [suite]
    dirs: List[str] = []

    for item in suites:
        if data_format == FORMAT_CSV:
            dirs.append(config.get_csv_dir(item))
        elif data_format == FORMAT_EXCEL:
            dirs.append(config.get_excel_dir(item))
        elif data_format == FORMAT_JSON:
            dirs.append(config.get_json_dir(item))
        elif data_format == FORMAT_ALL:
            dirs.extend([
                config.get_csv_dir(item),
                config.get_excel_dir(item),
                config.get_json_dir(item),
            ])

    return sorted(set(dirs))


def resolve_file_paths(
    config: Config,
    data_format: str,
    suite: str,
    single_file: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    """
    解析待加载的文件路径列表。

    Returns:
        (file_paths, scan_dirs)
    """
    if single_file:
        if os.path.isabs(single_file):
            path = single_file
        else:
            path = os.path.join(config.base_dir, single_file)
        return [path], []

    scan_dirs = get_scan_dirs(config, data_format, suite)
    file_paths: List[str] = []

    if data_format in (FORMAT_CSV, FORMAT_ALL):
        file_paths.extend(config.get_csv_test_files(suite))
    if data_format in (FORMAT_EXCEL, FORMAT_ALL):
        file_paths.extend(config.get_excel_test_files(suite))
    if data_format in (FORMAT_JSON, FORMAT_ALL):
        file_paths.extend(config.get_json_test_files(suite))

    return sorted(set(file_paths)), scan_dirs


def _detect_format(file_path: str) -> str:
    lower = file_path.lower()
    if lower.endswith(".csv"):
        return FORMAT_CSV
    if lower.endswith((".xlsx", ".xls")):
        return FORMAT_EXCEL
    if lower.endswith(".json"):
        return FORMAT_JSON
    return "unknown"


def discover_and_load(
    data_format: str,
    suite: Optional[str] = None,
    single_file: Optional[str] = None,
    env_names: Optional[List[str]] = None,
    load_cases: bool = True,
) -> DiscoveryResult:
    """
    发现并加载测试用例。

    Args:
        data_format: csv / excel / json / all
        suite: manual / ai / smoke
        single_file: 指定单文件时忽略目录扫描
        env_names: 环境 profile（影响 Config base_url）
        load_cases: 是否读取用例内容
    """
    config = Config(env_names=env_names)
    resolved_suite = resolve_suite(suite, single_file)
    file_paths, scan_dirs = resolve_file_paths(
        config, data_format, resolved_suite, single_file
    )

    result = DiscoveryResult(
        suite=resolved_suite,
        data_format=data_format,
        scan_dirs=scan_dirs,
        single_file=single_file or "",
    )

    reader = DataHandler()
    for file_path in file_paths:
        exists = os.path.isfile(file_path)
        fmt = _detect_format(file_path)
        case_count = 0
        cases: List[dict] = []

        if exists and load_cases:
            cases = reader.read_test_cases(file_path)
            rel = _relative_path(file_path)
            for case in cases:
                case["_source_file"] = file_path
                case["_format"] = fmt
                case["_unique_id"] = f"{rel}#{case['case_id']}"
            case_count = len(cases)
            result.cases.extend(cases)
        elif exists:
            case_count = -1  # 未加载，仅统计文件

        result.files.append(
            FileDiscovery(
                path=file_path,
                case_count=case_count,
                data_format=fmt,
                exists=exists,
            )
        )

    log_discovery(result)
    return result


def log_discovery(result: DiscoveryResult) -> None:
    """输出发现日志（CLI 模式下仅写文件，控制台已有 plan 摘要）。"""
    import os

    level = logging.DEBUG if os.getenv("IFRIT_CLI_MODE") == "1" else logging.INFO
    if result.single_file:
        logger.log(
            level,
            "用例发现 | 格式=%s 套件=%s 单文件=%s",
            result.data_format,
            result.suite,
            result.single_file,
        )
    else:
        dirs = ", ".join(result.scan_dirs) or "(未扫描目录)"
        logger.log(
            level,
            "用例发现 | 格式=%s 套件=%s 扫描目录=%s",
            result.data_format,
            result.suite,
            dirs,
        )

    if not result.files:
        logger.warning(
            "未发现任何 %s 用例文件（套件=%s）。"
            "AI 用例请使用 --suite ai；冒烟用例请使用 --suite smoke；全部请用 --suite all。",
            result.data_format.upper(),
            result.suite,
        )
        return

    logger.log(level, "发现 %s 个文件:", result.total_files)
    for item in result.files:
        rel = _relative_path(item.path)
        if not item.exists:
            logger.warning("  [缺失] %s", rel)
        elif item.case_count >= 0:
            logger.log(level, "  %s (%s 条) <- %s", rel, item.case_count, item.data_format)
        else:
            logger.log(level, "  %s <- %s", rel, item.data_format)

    if result.cases:
        logger.log(level, "合计加载 %s 条用例", result.total_cases)


def _relative_path(path: str) -> str:
    base = Config().base_dir
    if path.startswith(base):
        return os.path.relpath(path, base).replace("\\", "/")
    return path.replace("\\", "/")


def build_case_param_id(case: dict) -> str:
    """生成 pytest 参数化唯一 ID（避免跨文件 case_id 冲突）。"""
    unique_id = case.get("_unique_id") or case.get("case_id", "")
    return f"{unique_id} · {case.get('case_name', '')}"


def format_cli_plan(
    data_format: Optional[str],
    suite: Optional[str],
    test_path: Optional[str],
    env_names: Optional[List[str]],
    global_auth: bool = False,
) -> str:
    """生成 CLI 执行前摘要（精简，适合 CI/CD）。"""
    fmt = data_format or ( _detect_format(test_path) if test_path else FORMAT_ALL )
    if test_path and fmt == FORMAT_ALL:
        fmt = _detect_format(test_path)

    discovery = discover_and_load(
        data_format=fmt,
        suite=suite,
        single_file=test_path,
        env_names=env_names,
        load_cases=True,
    )

    env_label = ",".join(env_names) if env_names else "environment"
    lines = [
        "[IFRIT] ── 执行计划 ──",
        f"[IFRIT] 格式={fmt} 套件={discovery.suite} 环境={env_label}"
        + (" 鉴权=global" if global_auth else ""),
    ]

    if discovery.is_empty:
        lines.append("[IFRIT] 用例=0 （未发现可执行用例，请检查 --suite / --file）")
    else:
        file_parts = []
        for item in discovery.files:
            if item.exists and item.case_count > 0:
                file_parts.append(f"{_relative_path(item.path)}({item.case_count})")
        suite_hint = ""
        if discovery.suite == Config.SUITE_MANUAL and fmt == FORMAT_CSV:
            suite_hint = " | 提示: --suite all 含 smoke/ai"
        lines.append(
            f"[IFRIT] 用例={discovery.total_cases} 文件={discovery.total_files} "
            f"来源={'; '.join(file_parts) or '指定文件'}{suite_hint}"
        )
        lines.append(f"[IFRIT] 详细日志=logs/daily/ 失败=logs/errors/")

    return "\n".join(lines)


def parse_pytest_result(stdout: str, stderr: str, exit_code: int) -> Dict[str, int]:
    """从 pytest 输出解析结果摘要。"""
    import re

    combined = f"{stdout}\n{stderr}"
    summary = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "exit_code": exit_code}

    patterns = {
        "passed": r"(\d+)\s+passed",
        "failed": r"(\d+)\s+failed",
        "skipped": r"(\d+)\s+skipped",
        "error": r"(\d+)\s+error",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            summary[key] = int(match.group(1))

    return summary


def format_cli_result(summary: Dict[str, int]) -> str:
    """生成 CLI 执行后摘要。"""
    status = "PASS" if summary.get("exit_code", 1) == 0 else "FAIL"
    return (
        f"[IFRIT] ── 执行结果 ── status={status} "
        f"passed={summary.get('passed', 0)} "
        f"failed={summary.get('failed', 0)} "
        f"skipped={summary.get('skipped', 0)} "
        f"exit={summary.get('exit_code', 1)}"
    )
