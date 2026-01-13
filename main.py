#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : test_api_csv_driver.py
# @Software: PyCharm
import argparse
import os
import platform
import subprocess
import sys
import time

# 设置环境变量以确保正确的字符编码
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

from utils.logger import logger
from config.config import Config


def run_ai_generation(args):
    """
    运行AI测试用例生成
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    try:
        logger.info("开始AI测试用例生成")
        
        # 检查必要参数
        if not args.input_doc:
            logger.error("使用AI生成功能时必须指定 --input-doc 参数")
            return 1
        
        if not os.path.exists(args.input_doc):
            logger.error(f"输入文档不存在: {args.input_doc}")
            return 1
        
        # 导入AI相关模块
        from config.ai_config import AIConfig
        from core.document_parser import DocumentParser
        from core.ai_client import AIClient
        from core.case_generator import CaseGenerator
        from core.template_engine import TemplateEngine
        from core.quality_validator import QualityValidator
        
        # 初始化配置
        ai_config = AIConfig()
        if not ai_config.validate_config():
            logger.error("AI配置验证失败，请检查配置文件")
            return 1
        
        openai_config = ai_config.get_openai_config()
        generation_config = ai_config.get_generation_config()
        prompt_templates = ai_config.get_prompt_templates()
        output_config = ai_config.get_output_config()
        
        # 初始化组件
        parser = DocumentParser()
        ai_client = AIClient(openai_config)
        generator = CaseGenerator(ai_client, generation_config, prompt_templates)
        template_engine = TemplateEngine()
        validator = QualityValidator()
        
        # 解析文档
        logger.info(f"解析输入文档: {args.input_doc}")
        apis = parser.parse_document(args.input_doc, args.swagger_endpoint)
        
        if not apis:
            logger.error("未能从文档中解析出任何API接口")
            return 1
        
        logger.info(f"成功解析出 {len(apis)} 个API接口")
        
        # 生成测试用例
        all_test_cases = []
        for api in apis:
            logger.info(f"为API {api['method']} {api['path']} 生成测试用例")
            cases = generator.generate_all_cases(api)
            all_test_cases.extend(cases)
        
        if not all_test_cases:
            logger.error("未能生成任何测试用例")
            return 1
        
        logger.info(f"总共生成了 {len(all_test_cases)} 个测试用例")
        
        # 质量验证
        if output_config.get('quality_check', True):
            logger.info("进行质量验证")
            validation_result = validator.validate_batch_cases(all_test_cases)
            
            if validation_result['invalid_cases'] > 0:
                logger.warning(f"发现 {validation_result['invalid_cases']} 个无效用例")
                
                # 显示错误信息
                for error in validation_result['errors'][:10]:  # 只显示前10个错误
                    logger.warning(f"  - {error}")
                
                # 生成修复建议
                suggestions = validator.generate_fix_suggestions(validation_result['errors'])
                if suggestions:
                    logger.info("修复建议:")
                    for suggestion in suggestions:
                        logger.info(f"  - {suggestion}")
            
            # 显示质量评分
            quality_score = validator.get_quality_score(validation_result)
            logger.info(f"质量评分: {quality_score['score']} ({quality_score['grade']}) - {quality_score['description']}")
        
        # 确定输出路径
        output_dir = args.output_dir or output_config.get('default_output_dir', 'data/ai_generated')
        
        # 根据格式确定子目录
        format_dirs = {
            'excel': 'excel_data',
            'csv': 'csv_data', 
            'json': 'json_data'
        }
        
        if args.output_format in format_dirs:
            output_dir = os.path.join(output_dir, format_dirs[args.output_format])
        
        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S") if output_config.get('add_timestamp', True) else ""
        prefix = output_config.get('file_prefix', 'ai_')
        
        doc_name = os.path.splitext(os.path.basename(args.input_doc))[0]
        
        # 确定正确的文件扩展名
        file_extension = 'xlsx' if args.output_format.lower() == 'excel' else args.output_format
        
        if timestamp:
            filename = f"{prefix}{doc_name}_{timestamp}.{file_extension}"
        else:
            filename = f"{prefix}{doc_name}.{file_extension}"
        
        output_path = os.path.join(output_dir, filename)
        
        # 检查文件冲突
        if os.path.exists(output_path):
            conflict_resolution = output_config.get('conflict_resolution', 'ask')
            
            if conflict_resolution == 'ask':
                response = input(f"文件 {output_path} 已存在，是否覆盖？(y/n): ")
                if response.lower() != 'y':
                    logger.info("用户取消操作")
                    return 0
            elif conflict_resolution == 'rename':
                counter = 1
                base_path = output_path
                while os.path.exists(output_path):
                    name, ext = os.path.splitext(base_path)
                    output_path = f"{name}_{counter}{ext}"
                    counter += 1
                logger.info(f"文件重命名为: {output_path}")
        
        # 保存文件
        success = template_engine.save_cases_to_file(all_test_cases, output_path, args.output_format)
        
        if success:
            logger.info(f"成功保存 {len(all_test_cases)} 个测试用例到: {output_path}")
            
            # 显示统计信息
            stats = generator.get_generation_summary()
            logger.info(f"AI调用统计: 调用次数={stats['ai_calls']}, 总耗时={stats['total_response_time']:.2f}秒, 平均耗时={stats['average_response_time']:.2f}秒, 消耗tokens={stats['total_tokens']}")
            
            return 0
        else:
            logger.error("保存测试用例失败")
            return 1
            
    except Exception as e:
        logger.error(f"AI生成过程中发生异常: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return 1


def run_tests(test_path=None, test_type=None, env_names=None):
    """
    运行测试
    
    Args:
        test_path (str): 指定测试文件路径
        test_type (str): 测试类型 (excel/csv/all)
        env_names (list): 环境名称列表
    """
    try:
        logger.info("开始执行API自动化测试")
        logger.info(f"测试路径: {test_path}")
        logger.info(f"测试类型: {test_type}")
        logger.info(f"运行环境: {env_names}")

        # 初始化配置，传入环境名称
        config = Config(env_names=env_names)

        # 确保报告目录存在
        os.makedirs("./reports/allure_reports", exist_ok=True)

        # 构建pytest命令
        cmd = [
            "pytest",
            "-v",
            "--alluredir=./reports/allure_reports",
            "--clean-alluredir"
        ]

        # 添加环境参数到pytest命令
        if env_names:
            for env_name in env_names:
                cmd.extend(["--env", env_name])

        # 根据参数添加测试路径
        if test_path:
            # 检查文件类型并选择合适的测试驱动
            if test_path.endswith(".csv"):
                cmd.insert(1, "testcases/test_api_csv_driver.py")
                logger.info(f"检测到CSV文件，运行CSV测试用例: {test_path}")
            elif test_path.endswith((".xlsx", ".xls")):
                cmd.insert(1, "testcases/test_api_excel_driver.py")
                logger.info(f"检测到Excel文件，运行Excel测试用例: {test_path}")
            elif test_path.endswith(".json"):
                cmd.insert(1, "testcases/test_api_json_driver.py")
                logger.info(f"检测到JSON文件，运行JSON测试用例: {test_path}")
            else:
                # 如果是Python测试文件，则直接运行
                cmd.insert(1, test_path)
                logger.info(f"运行指定测试文件: {test_path}")
        elif test_type == "excel":
            cmd.insert(1, "testcases/test_api_excel_driver.py")
            logger.info("运行Excel测试用例")
        elif test_type == "csv":
            cmd.insert(1, "testcases/test_api_csv_driver.py")
            logger.info("运行CSV测试用例")
        elif test_type == "json":
            cmd.insert(1, "testcases/test_api_json_driver.py")
            logger.info("运行JSON测试用例")
        else:
            cmd.insert(1, "testcases/")
            logger.info("运行所有测试用例")

        # 执行测试
        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info(cmd)
        # 根据操作系统类型决定是否使用shell=True
        if platform.system().lower() == 'windows':
            logger.info("当前操作系统为Windows，使用shell=True")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            logger.info("当前操作系统为'Unix-like', 正常执行")
            result = subprocess.run(cmd, capture_output=True, text=True)

        # 输出结果
        logger.info("测试执行完成")
        logger.debug(f"标准输出:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"错误输出:\n{result.stderr}")

        logger.info(f"测试执行完成，退出码: {result.returncode}")
        return result.returncode

    except Exception as e:
        logger.error(f"执行测试时发生异常: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return 1


def serve_report():
    """
    启动Allure报告服务器
    """
    try:
        # 检查allure_reports目录是否存在且不为空
        if not os.path.exists("./reports/allure_reports"):
            logger.error("Allure报告目录不存在: ./reports/allure_reports")
            return

        if not os.listdir("./reports/allure_reports"):
            logger.warning("Allure报告目录为空，没有可显示的报告")
            return

        logger.info("启动Allure报告服务器")
        cmd = ["allure", "serve", "./reports/allure_reports"]
        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info(cmd)
        # 根据操作系统类型决定是否使用shell=True
        if platform.system().lower() == 'windows':
            subprocess.run(cmd, shell=True)
        else:
            subprocess.run(cmd)
    except FileNotFoundError:
        logger.error("未找到allure命令，请确保已安装Allure命令行工具")
    except Exception as e:
        logger.error(f"启动Allure报告服务器时发生异常: {str(e)}")


def generate_html_report():
    """
    生成HTML格式的Allure报告
    """
    try:
        # 确保输出目录存在
        os.makedirs("./reports/html", exist_ok=True)

        # 检查allure_reports目录是否存在且不为空
        if not os.path.exists("./reports/allure_reports"):
            logger.error("Allure报告目录不存在: ./reports/allure_reports")
            return False

        if not os.listdir("./reports/allure_reports"):
            logger.warning("Allure报告目录为空，没有可生成的报告")
            return False

        logger.info("生成HTML格式的Allure报告")
        cmd = ["allure", "generate", "./reports/allure_reports", "-o", "./reports/html", "--clean"]
        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info(cmd)
        # 根据操作系统类型决定是否使用shell=True
        if platform.system().lower() == 'windows':
            logger.info("当前操作系统为Windows，使用shell=True")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                                  env=dict(os.environ, LANG='zh_CN.UTF-8', LC_ALL='zh_CN.UTF-8'))
        else:
            logger.info("当前操作系统为'Unix-like', 正常执行")
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  env=dict(os.environ, LANG='zh_CN.UTF-8', LC_ALL='zh_CN.UTF-8'))
        if result.returncode == 0:
            logger.info("HTML报告生成成功，路径: ./reports/html")
            
            # 添加测试统计信息
            try:
                # 读取统计数据
                summary_file = "./reports/html/history/history-trend.json"
                if os.path.exists(summary_file):
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        import json
                        history_data = json.load(f)
                        if history_data and isinstance(history_data, list) and len(history_data) > 0:
                            latest = history_data[-1]['data']
                            total = latest['total']
                            passed = latest['passed']
                            failed = latest['failed']
                            skipped = latest['skipped']
                            broken = latest['broken']
                            
                            # logger.info("=" * 50)
                            # logger.info("测试执行汇总")
                            # logger.info("=" * 50)
                            # logger.info(f"总计执行用例数: {total}")
                            # logger.info(f"  通过: {passed}")
                            # logger.info(f"  失败: {failed}")
                            # logger.info(f"  跳过: {skipped}")
                            # logger.info(f"  错误: {broken}")
                            # logger.info("=" * 50)
                            logger.info(f"总计执行用例数: {total}, 通过: {passed}, 失败: {failed}, 跳过: {skipped}, 错误: {broken}")
                        else:
                            logger.warning("无法读取测试统计数据")
                else:
                    logger.warning("测试统计数据文件不存在")
            except Exception as e:
                logger.error(f"读取测试统计数据时发生异常: {str(e)}")
            
            return True
        else:
            logger.error(f"HTML报告生成失败: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("未找到allure命令，请确保已安装Allure命令行工具")
        return False
    except Exception as e:
        logger.error(f"生成HTML报告时发生异常: {str(e)}")
        return False


def main():
    """
    主函数
    """
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
        help="指定输出目录（默认：data/ai_generated）"
    )

    args = parser.parse_args()

    logger.info("解析命令行参数完成")
    logger.info(
        f"参数详情: serve_report={args.serve_report}, generate_report={args.generate_report}, type={args.type}, file={args.file}, env={args.env}, ai_generate={args.ai_generate}")

    # 如果启用AI生成功能
    if args.ai_generate:
        return run_ai_generation(args)
    
    # 运行测试
    exit_code = run_tests(test_path=args.file, test_type=args.type, env_names=args.env)

    # 如果指定了--serve-report参数，则启动报告服务器
    if args.serve_report:
        logger.info("用户指定了 --serve-report 参数，将启动报告服务器")
        serve_report()
    # 如果测试执行成功且指定了生成报告，则生成HTML报告
    elif args.generate_report or exit_code == 0:
        logger.info("测试执行完成，将生成HTML报告")
        generate_html_report()

    sys.exit(exit_code)  # 直接运行主函数需要注释掉本行sys.exit(exit_code)


if __name__ == "__main__":
    main()
    # 根据操作系统类型决定是否使用shell=True
    # if platform.system().lower() == 'windows':
    #     os.system("allurec/bin/allure generate reports/allure_reports -o reports/html --clean")
    #     os.system("allurec/bin/allure open reports/html")
    # else:
    #     os.system("allurec/bin/allure generate reports/allure_reports -o reports/html --clean")
    #     os.system("allurec/bin/allure open reports/html")