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
import sys

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """全局配置类"""

    def __init__(self, env_names=None):
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
        # 设置当前环境
        self.current_envs = env_names or ['environment']
        
        print(f"Config initialized with envs: {self.current_envs}")  # 调试信息
        
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
        # 遍历所有指定的环境，返回第一个有效的base_url
        for env in self.current_envs:
            if self.env_config.has_section(env) and self.env_config.has_option(env, 'base_url'):
                base_url = self.env_config.get(env, 'base_url')
                print(f"Using base_url from [{env}]: {base_url}")  # 调试信息
                return base_url
        # 默认返回environment部分的base_url
        base_url = self.env_config.get('environment', 'base_url', fallback='')
        print(f"Using default base_url from [environment]: {base_url}")  # 调试信息
        return base_url

    def get_timeout(self):
        """获取超时时间"""
        # 遍历所有指定的环境，返回第一个有效的timeout
        for env in self.current_envs:
            if self.env_config.has_section(env) and self.env_config.has_option(env, 'timeout'):
                timeout = self.env_config.getint(env, 'timeout')
                print(f"Using timeout from [{env}]: {timeout}")  # 调试信息
                return timeout
        # 默认返回environment部分的timeout
        timeout = self.env_config.getint('environment', 'timeout', fallback=30)
        print(f"Using default timeout from [environment]: {timeout}")  # 调试信息
        return timeout

    def get_log_level(self):
        """获取日志级别"""
        return self.env_config.get('logging', 'level', fallback='INFO')

    def get_test_files(self):
        """获取测试文件列表"""
        files = self.test_data_config.get('test_files', 'files', fallback='all')
        if files.lower() == 'all':
            return 'all'
        file_list = [f.strip() for f in files.split(',')]
        # 确保返回绝对路径
        data_dir = self.get_data_dir()
        return [os.path.join(data_dir, f) if not os.path.isabs(f) else f for f in file_list]

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

    def get_excel_test_files(self) -> List[str]:
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

        return test_files

    def get_csv_test_files(self) -> List[str]:
        """
        获取所有测试文件路径

        Returns:
            List[str]: 所有测试文件的路径列表
        """
        test_files = []

        # 获取CSV文件
        csv_dir = self.get_csv_dir()
        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    test_files.append(os.path.join(csv_dir, file))

        return test_files

    def get_json_dir(self):
        """获取JSON文件目录"""
        json_dir = self.test_data_config.get('json_files', 'json_dir', fallback='data/json_data')
        return os.path.join(self.base_dir, json_dir)

    def get_json_test_files(self) -> List[str]:
        """
        获取所有JSON测试文件路径

        Returns:
            List[str]: 所有JSON测试文件的路径列表
        """
        test_files = []

        # 获取JSON文件
        json_dir = self.get_json_dir()
        if os.path.exists(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith('.json'):
                    test_files.append(os.path.join(json_dir, file))

        return test_files


if __name__ == '__main__':
    print(Config().get_json_test_files())
    print(Config().get_json_test_files())