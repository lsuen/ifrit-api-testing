#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行界面管理器
负责处理命令行参数解析和分发
"""

import argparse
import sys


class CLIManager:
    """命令行界面管理器"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """创建命令行参数解析器"""
        parser = argparse.ArgumentParser(description="接口自动化测试框架")
        parser.add_argument(
            "--serve-report",
            action="store_true",
            help="运行测试并启动Allure报告服务器"
        )
        parser.add_argument(
            "--generate-report",
            action="store_true",
            help="生成HTML格式的Allure报告"
        )
        parser.add_argument(
            "--type",
            choices=["excel", "csv", "all", "json"],
            help="指定测试类型: excel/csv/all/json"
        )
        parser.add_argument(
            "--file",
            help="指定测试文件路径"
        )
        parser.add_argument(
            "--env",
            action="append",
            help="指定运行环境，可以多次使用以指定多个环境，如 --env dev --env prod"
        )
        
        # AI功能相关参数
        parser.add_argument(
            "--ai-generate",
            action="store_true",
            help="启用AI测试用例生成功能"
        )
        parser.add_argument(
            "--input-doc",
            help="指定输入文档路径（支持Markdown、Swagger JSON/YAML格式）"
        )
        parser.add_argument(
            "--input-url",
            help="指定远程接口文档 URL（Apifox MD / Swagger JSON 等）"
        )
        parser.add_argument(
            "--skill",
            help="AI Skill 名称（如 case_generation、doc_url_generation）"
        )
        parser.add_argument(
            "--swagger-endpoint",
            action="append",
            help="指定要解析的Swagger端点，可以多次使用"
        )
        parser.add_argument(
            "--output-format",
            choices=["excel", "csv", "json"],
            default="csv",
            help="指定生成的测试用例格式（默认：csv）"
        )
        parser.add_argument(
            "--output-dir",
            help="指定输出目录（默认：fixtures/ai/csv）"
        )
        parser.add_argument(
            "--suite",
            choices=["manual", "ai", "smoke", "all"],
            help="用例套件：manual/ai/smoke/all（传给 pytest）"
        )
        parser.add_argument(
            "--global-auth",
            action="store_true",
            help="启用全局鉴权（session 登录）"
        )
        parser.add_argument(
            "--clean",
            choices=["logs", "reports", "all"],
            help="清理过期日志或报告（不执行测试）"
        )
        parser.add_argument(
            "--keep-days",
            type=int,
            help="清理时覆盖 app.ini 中的保留天数"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅预览将被清理的文件，不实际删除"
        )
        parser.add_argument(
            "--chat",
            nargs=argparse.REMAINDER,
            help="进入 AI 交互模式；可选跟随单行命令，如 --chat doc api.json generate"
        )

        # 导入中心
        parser.add_argument(
            "--import",
            dest="import_file",
            metavar="FILE",
            help="导入外部测试文件（Postman Collection 等）",
        )
        parser.add_argument(
            "--import-format",
            choices=["postman"],
            default="postman",
            help="导入格式（默认 postman）",
        )
        parser.add_argument(
            "--import-suite",
            choices=["smoke", "manual", "ai"],
            default="manual",
            help="导入后归属套件目录（默认 manual）",
        )
        parser.add_argument(
            "--import-output",
            help="输出 CSV 路径（默认 fixtures/<suite>/csv/postman_<name>_<时间>.csv）",
        )
        parser.add_argument(
            "--import-ai-enhance",
            action="store_true",
            help="导入后 AI 增强（Postman 纯转换模式下预留）",
        )
        parser.add_argument(
            "--import-dry-run",
            action="store_true",
            help="仅预览导入结果，不写 CSV",
        )
        parser.add_argument(
            "--import-preview-only",
            action="store_true",
            help="解析并输出预览 JSON（stdout IMPORT_PREVIEW_JSON）",
        )
        parser.add_argument(
            "--import-diagnose",
            action="store_true",
            help="解析后用 LLM 诊断并建议追加用例",
        )
        parser.add_argument(
            "--inject-project-context",
            action="store_true",
            help="诊断时注入项目配置摘要",
        )
        parser.add_argument(
            "--import-output-format",
            choices=["csv", "json"],
            default="csv",
            help="输出用例文件格式（默认 csv）",
        )
        parser.add_argument(
            "--import-payload",
            metavar="FILE",
            help="保存合并用例的 JSON payload 文件",
        )
        parser.add_argument(
            "--project-root",
            default=".",
            help="项目根目录（诊断注入上下文时使用）",
        )

        return parser
    
    def parse_args(self):
        """解析命令行参数"""
        return self.parser.parse_args()
    
    def run(self):
        """运行CLI应用"""
        from core.test_runner import TestRunner
        from core.report_manager import ReportManager
        from core.retention import (
            clean_all,
            clean_logs,
            clean_reports,
            format_clean_summary,
        )
        from agent.pipeline.generator import AIGenerator
        from core.importers.runner import run_import

        args = self.parse_args()

        if args.import_file:
            sys.exit(run_import(args))
        if args.import_payload:
            sys.exit(run_import(args))

        if args.chat is not None:
            from agent.pipeline.chat import AIChatSession

            chat_argv = [item for item in (args.chat or []) if item != "--"]
            session = AIChatSession()
            sys.exit(session.run(chat_argv or None))

        if args.clean:
            if args.clean == "logs":
                results = [clean_logs(keep_days=args.keep_days, dry_run=args.dry_run)]
            elif args.clean == "reports":
                results = [
                    clean_reports(keep_days=args.keep_days, dry_run=args.dry_run)
                ]
            else:
                results = clean_all(keep_days=args.keep_days, dry_run=args.dry_run)
            print(format_clean_summary(results))
            sys.exit(0)

        # 如果启用AI生成功能
        if args.ai_generate:
            generator = AIGenerator(skill_name=args.skill)
            exit_code = generator.run(args)
            sys.exit(exit_code)
        
        # 运行测试
        runner = TestRunner()
        exit_code = runner.run(
            test_path=args.file,
            test_type=args.type,
            env_names=args.env,
            suite=args.suite,
            global_auth=args.global_auth,
        )

        # 如果指定了--serve-report参数，则启动报告服务器
        if args.serve_report:
            report_manager = ReportManager()
            report_manager.serve_report()
        # 如果测试执行成功且指定了生成报告，则生成HTML报告
        elif args.generate_report or exit_code == 0:
            from utils.logger import configure_logging, set_console_level
            import logging

            set_console_level(logging.WARNING)
            report_manager = ReportManager()
            report_ok = report_manager.generate_html_report()
            configure_logging(console_level=logging.INFO)
            if report_ok:
                print(f"[IFRIT] 报告={report_manager.latest_report_path()}")

        sys.exit(exit_code)