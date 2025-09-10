#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : test_api_csv_driver.py
# @Software: PyCharm
import configparser
import os
from typing import Dict, Any, List

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """全局配置类"""

    def __init__(self):
        self.base_dir = BASE_DIR
        self.config_dir = os.path.join(BASE_DIR, 'config')
        self.data_dir = os.path.join(BASE_DIR, 'data')
        self.logs_dir = os.path.join(BASE_DIR, 'logs')
        self.reports_dir = os.path.join(BASE_DIR, 'reports')
        self.testcases_dir = os.path.join(BASE_DIR, 'testcases')
        self.utils_dir = os.path.join(BASE_DIR, 'utils')
        self.core_dir = os.path.join(BASE_DIR, 'core')

        # 创建必要的目录
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # 加载环境配置
        self.env_config = self._load_env_config()
        # 加载测试数据配置
        self.test_data_config = self._load_test_data_config()

    def _load_env_config(self) -> Dict[str, Any]:
        """加载环境配置"""
        config = configparser.ConfigParser()
        env_config_path = os.path.join(self.config_dir, 'env_config.ini')
        config.read(env_config_path, encoding='utf-8')
        return config

    def _load_test_data_config(self) -> Dict[str, Any]:
        """加载测试数据配置"""
        config = configparser.ConfigParser()
        test_data_config_path = os.path.join(self.config_dir, 'test_data_config.ini')
        config.read(test_data_config_path, encoding='utf-8')
        return config

    def get_base_url(self):
        """获取基础URL"""
        return self.env_config.get('environment', 'base_url', fallback='')

    def get_timeout(self):
        """获取超时时间"""
        return self.env_config.getint('environment', 'timeout', fallback=30)

    def get_log_level(self):
        """获取日志级别"""
        return self.env_config.get('logging', 'level', fallback='INFO')

    def get_test_files(self):
        """获取测试文件列表"""
        files = self.test_data_config.get('test_files', 'files', fallback='all')
        if files.lower() == 'all':
            return 'all'
        return [f.strip() for f in files.split(',')]

    def get_data_dir(self):
        """获取测试数据目录"""
        data_dir = self.test_data_config.get('test_files', 'data_dir', fallback='data')
        return os.path.join(self.base_dir, data_dir)

    def get_excel_dir(self):
        """获取Excel文件目录"""
        excel_dir = self.test_data_config.get('excel_files', 'excel_dir', fallback='data/excel_data')
        return os.path.join(self.base_dir, excel_dir)

    def get_csv_dir(self):
        """获取CSV文件目录"""
        csv_dir = self.test_data_config.get('csv_files', 'csv_dir', fallback='data/csv_data')
        return os.path.join(self.base_dir, csv_dir)

    def get_all_test_files(self) -> List[str]:
        """
        获取所有测试文件路径
        
        Returns:
            List[str]: 所有测试文件的路径列表
        """
        test_files = []
        
        # 获取Excel文件
        excel_dir = self.get_excel_dir()
        if os.path.exists(excel_dir):
            for file in os.listdir(excel_dir):
                if file.endswith(('.xlsx', '.xls')):
                    test_files.append(os.path.join(excel_dir, file))
        
        # 获取CSV文件
        csv_dir = self.get_csv_dir()
        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    test_files.append(os.path.join(csv_dir, file))
        
        return test_files