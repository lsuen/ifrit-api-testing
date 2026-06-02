#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : logger.py
# @Software: PyCharm
import logging
import os
from datetime import datetime
import sys
from pathlib import Path

from config.config import Config

# 创建日志目录（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

class EnhancedLogger:
    """增强的日志记录器类"""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.config = Config()
        self.current_date = datetime.now().strftime("%Y%m%d")
        self.setup_handlers()
    
    def setup_handlers(self):
        """设置日志处理器"""
        # 清除现有的处理器
        self.logger.handlers.clear()
        self.logger.setLevel(logging.DEBUG)
        
        # 通用格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 1. 总日志文件 - 存储所有日志
        main_log_path = os.path.join(log_dir, 'api_automation.log')
        main_handler = logging.FileHandler(main_log_path, encoding='utf-8')
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(main_handler)
        
        # 2. 按天分割的日志文件（可配置开关）
        daily_logs_enabled = self.config.app_config.getboolean(
            'logging', 'daily_logs_enabled', fallback=True
        )
        if daily_logs_enabled:
            daily_log_path = os.path.join(log_dir, 'daily')
            os.makedirs(daily_log_path, exist_ok=True)
            # 按天命名的日志处理器（每天创建一个新文件）
            daily_log_file = os.path.join(daily_log_path, f'daily_{self.current_date}.log')
            daily_handler = logging.FileHandler(daily_log_file, encoding='utf-8')
            daily_handler.setFormatter(formatter)
            daily_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(daily_handler)
        
        # 3. 错误日志按天单独存储（可配置开关）
        error_daily_logs_enabled = self.config.app_config.getboolean(
            'logging', 'error_daily_logs_enabled', fallback=True
        )
        if error_daily_logs_enabled:
            error_daily_log_path = os.path.join(log_dir, 'errors')
            os.makedirs(error_daily_log_path, exist_ok=True)
            # 专门记录错误的按天命名日志处理器
            error_daily_log_file = os.path.join(error_daily_log_path, f'error_{self.current_date}.log')
            error_daily_handler = logging.FileHandler(error_daily_log_file, encoding='utf-8')
            error_daily_handler.setFormatter(formatter)
            error_daily_handler.setLevel(logging.ERROR)  # 只记录错误及以上级别
            # 添加过滤器，只处理错误级别及以上的消息
            class ErrorFilter(logging.Filter):
                def filter(self, record):
                    return record.levelno >= logging.ERROR
            error_daily_handler.addFilter(ErrorFilter())
            self.logger.addHandler(error_daily_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

# 全局日志记录器实例
_enhanced_logger = EnhancedLogger()
logger = _enhanced_logger.logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器实例

    Args:
        name (str): 日志记录器名称，默认为模块名

    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        name = __name__
    return logger  # 返回全局logger实例，保持一致性