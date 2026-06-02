#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试执行器
负责执行API自动化测试
"""

import os
import platform
import subprocess
import logging
from config.config import Config


class TestRunner:
    """测试执行器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run(self, test_path=None, test_type=None, env_names=None, suite=None, global_auth=False):
        """
        运行测试
        
        Args:
            test_path (str): 指定测试文件路径
            test_type (str): 测试类型 (excel/csv/all)
            env_names (list): 环境名称列表
        """
        try:
            self.logger.info("开始执行API自动化测试")
            self.logger.info(f"测试路径: {test_path}")
            self.logger.info(f"测试类型: {test_type}")
            self.logger.info(f"运行环境: {env_names}")

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

            if test_path and test_path.endswith((".csv", ".xlsx", ".xls", ".json")):
                cmd.extend(["--test-data-file", test_path])

            if suite:
                cmd.extend(["--suite", suite])
            elif test_path and "fixtures/ai" in test_path.replace("\\", "/"):
                cmd.extend(["--suite", "ai"])
            elif test_path and "fixtures/smoke" in test_path.replace("\\", "/"):
                cmd.extend(["--suite", "smoke"])

            if global_auth:
                cmd.append("--global-auth")

            # 根据参数添加测试路径
            if test_path:
                # 检查文件类型并选择合适的测试驱动
                if test_path.endswith(".csv"):
                    cmd.insert(1, "drivers/test_api_csv_driver.py")
                    self.logger.info(f"检测到CSV文件，运行CSV测试用例: {test_path}")
                elif test_path.endswith((".xlsx", ".xls")):
                    cmd.insert(1, "drivers/test_api_excel_driver.py")
                    self.logger.info(f"检测到Excel文件，运行Excel测试用例: {test_path}")
                elif test_path.endswith(".json"):
                    cmd.insert(1, "drivers/test_api_json_driver.py")
                    self.logger.info(f"检测到JSON文件，运行JSON测试用例: {test_path}")
                else:
                    # 如果是Python测试文件，则直接运行
                    cmd.insert(1, test_path)
                    self.logger.info(f"运行指定测试文件: {test_path}")
            elif test_type == "excel":
                cmd.insert(1, "drivers/test_api_excel_driver.py")
                self.logger.info("运行Excel测试用例")
            elif test_type == "csv":
                cmd.insert(1, "drivers/test_api_csv_driver.py")
                self.logger.info("运行CSV测试用例")
            elif test_type == "json":
                cmd.insert(1, "drivers/test_api_json_driver.py")
                self.logger.info("运行JSON测试用例")
            else:
                cmd.insert(1, "drivers/")
                self.logger.info("运行所有测试用例")

            # 执行测试
            self.logger.info(f"执行命令: {' '.join(cmd)}")
            # 根据操作系统类型决定是否使用shell=True
            if platform.system().lower() == 'windows':
                self.logger.info("当前操作系统为Windows，使用shell=True")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                self.logger.info("当前操作系统为'Unix-like', 正常执行")
                result = subprocess.run(cmd, capture_output=True, text=True)

            # 输出结果
            self.logger.info("测试执行完成")
            self.logger.debug(f"标准输出:\n{result.stdout}")
            if result.stderr:
                self.logger.debug(f"错误输出:\n{result.stderr}")

            self.logger.info(f"测试执行完成，退出码: {result.returncode}")
            return result.returncode

        except Exception as e:
            self.logger.error(f"执行测试时发生异常: {str(e)}")
            import traceback
            self.logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return 1