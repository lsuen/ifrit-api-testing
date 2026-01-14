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


class ReportManager:
    """报告管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def serve_report(self):
        """
        启动Allure报告服务器
        """
        try:
            # 检查allure_reports目录是否存在且不为空
            if not os.path.exists("./reports/allure_reports"):
                self.logger.error("Allure报告目录不存在: ./reports/allure_reports")
                return

            if not os.listdir("./reports/allure_reports"):
                self.logger.warning("Allure报告目录为空，没有可显示的报告")
                return

            self.logger.info("启动Allure报告服务器")
            cmd = ["allure", "serve", "./reports/allure_reports"]
            self.logger.info(f"执行命令: {' '.join(cmd)}")
            # 根据操作系统类型决定是否使用shell=True
            if platform.system().lower() == 'windows':
                subprocess.run(cmd, shell=True)
            else:
                subprocess.run(cmd)
        except FileNotFoundError:
            self.logger.error("未找到allure命令，请确保已安装Allure命令行工具")
        except Exception as e:
            self.logger.error(f"启动Allure报告服务器时发生异常: {str(e)}")

    def generate_html_report(self):
        """
        生成HTML格式的Allure报告
        """
        try:
            # 确保输出目录存在
            os.makedirs("./reports/html", exist_ok=True)

            # 检查allure_reports目录是否存在且不为空
            if not os.path.exists("./reports/allure_reports"):
                self.logger.error("Allure报告目录不存在: ./reports/allure_reports")
                return False

            if not os.listdir("./reports/allure_reports"):
                self.logger.warning("Allure报告目录为空，没有可生成的报告")
                return False

            self.logger.info("生成HTML格式的Allure报告")
            cmd = ["allure", "generate", "./reports/allure_reports", "-o", "./reports/html", "--clean"]
            self.logger.info(f"执行命令: {' '.join(cmd)}")
            # 根据操作系统类型决定是否使用shell=True
            if platform.system().lower() == 'windows':
                self.logger.info("当前操作系统为Windows，使用shell=True")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                                      env=dict(os.environ, LANG='zh_CN.UTF-8', LC_ALL='zh_CN.UTF-8'))
            else:
                self.logger.info("当前操作系统为'Unix-like', 正常执行")
                result = subprocess.run(cmd, capture_output=True, text=True,
                                      env=dict(os.environ, LANG='zh_CN.UTF-8', LC_ALL='zh_CN.UTF-8'))
            if result.returncode == 0:
                self.logger.info("HTML报告生成成功，路径: ./reports/html")
                
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
                                
                                self.logger.info(f"总计执行用例数: {total}, 通过: {passed}, 失败: {failed}, 跳过: {skipped}, 错误: {broken}")
                            else:
                                self.logger.warning("无法读取测试统计数据")
                    else:
                        self.logger.warning("测试统计数据文件不存在")
                except Exception as e:
                    self.logger.error(f"读取测试统计数据时发生异常: {str(e)}")
                
                return True
            else:
                self.logger.error(f"HTML报告生成失败: {result.stderr}")
                return False
        except FileNotFoundError:
            self.logger.error("未找到allure命令，请确保已安装Allure命令行工具")
            return False
        except Exception as e:
            self.logger.error(f"生成HTML报告时发生异常: {str(e)}")
            return False