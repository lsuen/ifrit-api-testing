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

# 设置环境变量以确保正确的字符编码
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

from utils.logger import logger
from config.config import Config


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

    args = parser.parse_args()

    logger.info("解析命令行参数完成")
    logger.info(
        f"参数详情: serve_report={args.serve_report}, generate_report={args.generate_report}, type={args.type}, file={args.file}, env={args.env}")

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