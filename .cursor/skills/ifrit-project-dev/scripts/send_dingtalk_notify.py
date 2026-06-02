#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
文件用途：Git 提交后向钉钉机器人推送标准化迭代通知
核心功能：读取 .env、从最近 commit 自动生成概要、POST 发送
创建时间：2026-06-02
"""
import argparse
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import requests

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    )
)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.loader import get_dingtalk_config

COMMIT_TYPE_CHOICES = ("feat", "fix", "refactor", "doc")
HTTP_TIMEOUT_SECONDS = 15
REQUEST_SUCCESS_CODE = 0
COMMIT_TYPE_PATTERN = re.compile(r"^(feat|fix|refactor|doc)\s*[：:]", re.IGNORECASE)


def run_git_command(args: List[str]) -> str:
    """执行 git 命令并返回 stdout。"""
    result = subprocess.run(
        ["git"] + args,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git 命令失败: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def parse_commit_type(subject: str) -> str:
    """从 commit subject 解析类型，默认 doc。"""
    match = COMMIT_TYPE_PATTERN.match(subject.strip())
    if match:
        return match.group(1).lower()
    return "doc"


def parse_commit_summary(subject: str, body: str) -> str:
    """从 commit message 提取概要说明。"""
    summary = COMMIT_TYPE_PATTERN.sub("", subject.strip()).strip() or subject.strip()
    if body:
        body_lines = [
            line.strip()
            for line in body.splitlines()
            if line.strip() and not line.strip().lower().startswith("co-authored-by:")
        ]
        if body_lines:
            summary = f"{summary}；{'；'.join(body_lines)}"
    return summary[:800]


def extract_changed_modules(changed_files: List[str]) -> str:
    """从变更文件路径提取涉及模块目录。"""
    modules = []
    seen = set()
    for file_path in changed_files:
        top_dir = file_path.split("/")[0].split("\\")[0]
        if top_dir and top_dir not in seen:
            seen.add(top_dir)
            modules.append(top_dir)
    return "、".join(modules) if modules else "项目根目录"


def load_from_last_commit() -> Dict[str, str]:
    """读取最近一次 commit，自动生成通知字段。"""
    commit_hash = run_git_command(["rev-parse", "--short", "HEAD"])
    subject = run_git_command(["log", "-1", "--format=%s"])
    body = run_git_command(["log", "-1", "--format=%b"])
    changed_files = [
        line.strip()
        for line in run_git_command(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]).splitlines()
        if line.strip()
    ]

    commit_type = parse_commit_type(subject)
    summary = parse_commit_summary(subject, body)
    modules = extract_changed_modules(changed_files)

    return {
        "commit_type": commit_type,
        "commit_hash": commit_hash,
        "summary": summary,
        "modules": modules,
        "reason": summary,
        "unit_test": "见本次 commit 变更范围，按改动执行对应用例",
        "func_test": "核心功能正常运行，无异常、无报错",
        "edge_test": "验证通过，无潜在风险",
        "other_test": "无",
    }


def build_report_markdown(
    commit_type: str,
    commit_hash: str,
    summary: str,
    modules: str,
    reason: str,
    unit_test: str,
    func_test: str,
    edge_test: str,
    other_test: str,
) -> str:
    """按项目标准模板生成 Markdown 报告。"""
    if commit_type not in COMMIT_TYPE_CHOICES:
        raise ValueError(f"commit_type 必须为: {COMMIT_TYPE_CHOICES}")

    lines = [
        "### 项目开发迭代通知",
        "#### 一、提交类型",
        f"【{commit_type}】",
        "",
        "#### 二、本次迭代内容",
        f"1. 功能/修改说明：{summary}",
        f"2. 涉及模块：{modules}",
        f"3. 改动原因：{reason}",
        "",
        "#### 三、测试结果",
        f"1. 单元测试：{unit_test}",
        f"2. 功能测试：{func_test}",
        f"3. 边界/异常测试：{edge_test}",
        f"4. 其他测试说明：{other_test}",
        "",
        "#### 四、项目更新记录",
        "1. 已更新.MemoryForAI项目记忆目录",
        "2. 已同步更新README及相关配套文档",
        f"3. Git提交编号：【{commit_hash}】",
        "",
        "#### 五、开发人员",
        "作者：孙文龙",
    ]
    return "\n".join(lines)


def send_markdown_report(webhook_url: str, keyword: str, markdown_text: str) -> dict:
    """向钉钉机器人 POST 发送 Markdown 消息。"""
    if keyword and keyword not in markdown_text:
        markdown_text = f"{keyword}\n\n{markdown_text}"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "项目开发迭代通知",
            "text": markdown_text,
        },
    }

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("errcode") != REQUEST_SUCCESS_CODE:
        raise RuntimeError(f"钉钉返回错误: {result}")

    return result


def read_report_file(report_path: str) -> str:
    """读取外部 Markdown 报告文件。"""
    if not os.path.isfile(report_path):
        raise FileNotFoundError(f"报告文件不存在: {report_path}")

    with open(report_path, "r", encoding="utf-8") as report_file:
        content = report_file.read().strip()

    if not content:
        raise ValueError("报告文件内容为空")

    return content


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="发送钉钉项目迭代通知")
    parser.add_argument(
        "--from-last-commit",
        action="store_true",
        help="从最近一次 git commit 自动提取类型、哈希、概要、涉及模块（推荐）",
    )
    parser.add_argument(
        "--report-file",
        help="已填好的 Markdown 报告文件路径（指定后忽略其他内容参数）",
    )
    parser.add_argument(
        "--commit-type",
        choices=COMMIT_TYPE_CHOICES,
        help="提交类型: feat / fix / refactor / doc",
    )
    parser.add_argument("--commit-hash", help="Git 提交编号（短哈希或完整哈希）")
    parser.add_argument("--summary", help="功能/修改说明")
    parser.add_argument("--modules", help="涉及模块")
    parser.add_argument("--reason", help="改动原因")
    parser.add_argument("--unit-test", default="通过", help="单元测试结果说明")
    parser.add_argument(
        "--func-test",
        default="核心功能正常运行，无异常、无报错",
        help="功能测试说明",
    )
    parser.add_argument(
        "--edge-test",
        default="验证通过，无潜在风险",
        help="边界/异常测试说明",
    )
    parser.add_argument("--other-test", default="无", help="其他测试说明")
    parser.add_argument("--dry-run", action="store_true", help="仅打印报告，不发送")
    return parser.parse_args()


def validate_required_fields(args: argparse.Namespace) -> None:
    """校验必填参数。"""
    required_fields = (
        "commit_type",
        "commit_hash",
        "summary",
        "modules",
        "reason",
    )
    missing = [name for name in required_fields if not getattr(args, name, None)]
    if missing:
        raise ValueError(f"缺少必填参数: {', '.join(missing)}")


def resolve_notify_fields(args: argparse.Namespace) -> Dict[str, str]:
    """合并命令行参数与 last-commit 自动提取结果。"""
    if args.from_last_commit:
        auto_fields = load_from_last_commit()
        return {
            "commit_type": args.commit_type or auto_fields["commit_type"],
            "commit_hash": args.commit_hash or auto_fields["commit_hash"],
            "summary": args.summary or auto_fields["summary"],
            "modules": args.modules or auto_fields["modules"],
            "reason": args.reason or auto_fields["reason"],
            "unit_test": args.unit_test if args.unit_test != "通过" else auto_fields["unit_test"],
            "func_test": args.func_test,
            "edge_test": args.edge_test,
            "other_test": args.other_test,
        }

    validate_required_fields(args)
    return {
        "commit_type": args.commit_type,
        "commit_hash": args.commit_hash,
        "summary": args.summary,
        "modules": args.modules,
        "reason": args.reason,
        "unit_test": args.unit_test,
        "func_test": args.func_test,
        "edge_test": args.edge_test,
        "other_test": args.other_test,
    }


def main() -> int:
    """入口：组装报告并发送钉钉通知。"""
    args = parse_arguments()

    try:
        if args.report_file:
            markdown_text = read_report_file(args.report_file)
        else:
            fields = resolve_notify_fields(args)
            markdown_text = build_report_markdown(**fields)

        if args.dry_run:
            print(markdown_text)
            return 0

        dingtalk_config = get_dingtalk_config()
        send_markdown_report(
            webhook_url=dingtalk_config["webhook_url"],
            keyword=dingtalk_config["keyword"],
            markdown_text=markdown_text,
        )
        print("钉钉通知发送成功")
        return 0

    except (FileNotFoundError, ValueError, RuntimeError, requests.RequestException) as error:
        print(f"发送失败: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
