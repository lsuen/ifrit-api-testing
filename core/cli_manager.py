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
            choices=["manual", "ai", "smoke"],
            help="用例套件：manual/ai/smoke（传给 pytest）"
        )
        parser.add_argument(
            "--global-auth",
            action="store_true",
            help="启用全局鉴权（session 登录）"
        )
        
        return parser
    
    def parse_args(self):
        """解析命令行参数"""
        return self.parser.parse_args()
    
    def run(self):
        """运行CLI应用"""
        from core.test_runner import TestRunner
        from core.report_manager import ReportManager
        from agent.pipeline.generator import AIGenerator
        
        args = self.parse_args()
        
        # 如果启用AI生成功能
        if args.ai_generate:
            generator = AIGenerator()
            return generator.run(args)
        
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
            report_manager = ReportManager()
            report_path = report_manager.generate_html_report()
            if report_path:
                print(f"[IFRIT] 报告=reports/html/index.html")

        sys.exit(exit_code)