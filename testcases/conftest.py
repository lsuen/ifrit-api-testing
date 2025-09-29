#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : test_api_csv_driver.py
# @Software: PyCharm
import logging
import os
import pytest
from core.request_handler import RequestHandler
from core.data_handler import DataHandler

# 设置环境变量以确保正确的字符编码
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# 用于存储环境参数的全局变量
ENV_NAMES = []


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--env",
        action="append",
        help="指定运行环境，可以多次使用以指定多个环境，如 --env dev --env prod"
    )


def pytest_configure(config):
    """配置pytest"""
    global ENV_NAMES
    ENV_NAMES = config.getoption("--env") or []
    print(f"Pytest configured with envs: {ENV_NAMES}")  # 调试信息


@pytest.fixture(scope="session")
def request_handler():
    """请求处理器fixture"""
    # 在request_handler中使用环境配置
    from config.config import Config
    logging.info(f"Creating request handler with envs: {ENV_NAMES}")  # 调试信息
    config = Config(env_names=ENV_NAMES)
    base_url = config.get_base_url()
    timeout = config.get_timeout()
    logging.info(f"Request handler base_url: {base_url}, timeout: {timeout}")  # 调试信息
    return RequestHandler(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="session")
def data_handler():
    """数据处理器fixture"""
    return DataHandler()


@pytest.fixture(scope="function", autouse=True)
def clear_data_handler(data_handler):
    """每个测试函数执行前清空全局变量"""
    data_handler.clear_global_vars()
    yield