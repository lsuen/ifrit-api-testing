#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
用途：全流程调试脚本 — probe → auth → AI 生成 → 冒烟/AI 验证 → prune
创建时间：2026-06-02

用法:
  python scripts/debug_workflow.py
  python scripts/debug_workflow.py --skip-generate
  python scripts/debug_workflow.py --endpoints /api/test /api/login
"""
import argparse
import glob
import logging
import os
import subprocess
import sys
import time
from types import SimpleNamespace

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.config import Config
from config.ai_config import AIConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("debug_workflow")


def run_cmd(cmd: list, cwd: str = PROJECT_ROOT) -> int:
    """执行子进程命令并返回 exit code。"""
    logger.info("执行: %s", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=cwd, check=False)
    return completed.returncode


def step_probe(base_url: str, endpoints: list, use_curl: bool) -> bool:
    """Step 1: 探测端点连通性。"""
    from agent.actions.probe_endpoint import ProbeEndpointAction

    logger.info("=== Step 1: 探测端点 ===")
    context = {
        "base_url": base_url,
        "endpoints": endpoints,
        "use_curl": use_curl,
    }
    result = ProbeEndpointAction().run(context)
    for item in result.get("probe_results", []):
        logger.info(
            "  %s -> status=%s ok=%s preview=%s",
            item["endpoint"],
            item.get("status_code"),
            item.get("ok"),
            (item.get("body_preview") or "")[:60],
        )
    return result.get("probe_ok", False)


def step_discover_auth(api_doc: str) -> None:
    """Step 2: 发现/重写鉴权配置。"""
    from agent.actions.discover_auth import DiscoverAuthAction

    logger.info("=== Step 2: 鉴权发现 ===")
    DiscoverAuthAction().run(
        {
            "api_doc": api_doc,
            "login_path_hint": "/api/login",
        }
    )


def step_generate(api_doc: str, endpoints: list, output_dir: str) -> str:
    """Step 3: AI 生成用例。"""
    from agent.pipeline.generator import AIGenerator

    logger.info("=== Step 3: AI 生成用例 ===")
    args = SimpleNamespace(
        input_doc=api_doc,
        swagger_endpoint=endpoints,
        output_format="csv",
        output_dir=output_dir,
    )
    exit_code = AIGenerator().run(args)
    if exit_code != 0:
        raise RuntimeError("AI 生成失败")

    output_config = AIConfig().get_output_config()
    return AIGenerator.get_last_output_path(args, output_config)


def step_run_tests(
    csv_path: str,
    env_names: list,
    global_auth: bool = False,
    suite: str = "ai",
) -> int:
    """Step 4: 运行指定 CSV 用例。"""
    logger.info("=== Step 4: 运行用例 %s (suite=%s) ===", csv_path, suite)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "drivers/test_api_csv_driver.py",
        "-v",
        "--test-data-file",
        csv_path,
        "--suite",
        suite,
    ]
    for env_name in env_names:
        cmd.extend(["--env", env_name])
    if global_auth:
        cmd.append("--global-auth")
    return run_cmd(cmd)


def step_prune(csv_path: str, env_names: list) -> int:
    """Step 5: 删除失败用例。"""
    from agent.actions.prune_failed_cases import PruneFailedCasesAction

    logger.info("=== Step 5: Prune 失败用例 ===")
    context = {"csv_path": csv_path, "env_names": env_names}
    result = PruneFailedCasesAction().run(context)
    logger.info("删除 %s 条失败用例", result.get("pruned_count", 0))
    return result.get("pruned_count", 0)


def find_latest_ai_csv(ai_dir: str) -> str:
    """查找最新 AI 生成 CSV。"""
    pattern = os.path.join(ai_dir, "ai_*.csv")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return files[0] if files else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="ifrit-apitest 全流程调试")
    parser.add_argument(
        "--api-doc",
        default="api_docs/apispec_1.json",
        help="Swagger 文档路径",
    )
    parser.add_argument(
        "--endpoints",
        nargs="+",
        default=["/api/test"],
        help="探测与生成的端点（默认只测 /api/test）",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=["environment"],
        help="运行环境 profile",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="跳过 AI 生成，使用已有 AI CSV",
    )
    parser.add_argument(
        "--skip-probe",
        action="store_true",
        help="跳过端点探测",
    )
    parser.add_argument(
        "--use-curl",
        action="store_true",
        help="探测时使用 curl（WSL/Linux 推荐）",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="验证失败后删除 AI CSV 中的失败行",
    )
    parser.add_argument(
        "--global-auth",
        action="store_true",
        help="AI 用例验证时启用全局鉴权",
    )
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    config = Config(env_names=args.env)
    base_url = config.get_base_url()
    api_doc = args.api_doc if os.path.isabs(args.api_doc) else os.path.join(PROJECT_ROOT, args.api_doc)
    smoke_csv = os.path.join(config.get_smoke_csv_dir(), "api_test_smoke.csv")
    ai_output_dir = config.get_ai_output_dir()

    logger.info("项目根目录: %s", PROJECT_ROOT)
    logger.info("被测 API: %s", base_url)

    if not args.skip_probe:
        if not step_probe(base_url, args.endpoints, args.use_curl):
            logger.error("端点探测失败，终止流程")
            return 1

    step_discover_auth(api_doc)

    if os.path.isfile(smoke_csv):
        logger.info("=== 冒烟测试 ===")
        smoke_code = step_run_tests(smoke_csv, args.env, global_auth=False, suite="smoke")
        if smoke_code != 0:
            logger.warning("冒烟测试未全部通过 (exit=%s)，继续后续步骤", smoke_code)
    else:
        logger.warning("冒烟用例不存在: %s", smoke_csv)

    ai_csv = ""
    if args.skip_generate:
        ai_csv = find_latest_ai_csv(ai_output_dir)
        if not ai_csv:
            logger.error("未找到 AI 生成 CSV，请先运行生成或去掉 --skip-generate")
            return 1
        logger.info("使用已有 AI 用例: %s", ai_csv)
    else:
        try:
            ai_csv = step_generate(api_doc, args.endpoints, ai_output_dir)
            logger.info("AI 用例已生成: %s", ai_csv)
        except RuntimeError as error:
            logger.error("%s", error)
            return 1

    ai_exit = step_run_tests(ai_csv, args.env, global_auth=args.global_auth, suite="ai")
    if ai_exit != 0 and args.prune:
        step_prune(ai_csv, args.env)
        logger.info("Prune 完成，可重新运行: python main.py --file %s --global-auth", ai_csv)

    logger.info("=== 全流程结束 ===")
    return ai_exit


if __name__ == "__main__":
    sys.exit(main())
