#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
# @Site    :
# @File    : test_api_csv_driver.py
# @Software: PyCharm
import pytest
from core.request_handler import RequestHandler
from core.data_handler import DataHandler


@pytest.fixture(scope="session")
def request_handler():
    """请求处理器fixture"""
    return RequestHandler()


@pytest.fixture(scope="session")
def data_handler():
    """数据处理器fixture"""
    return DataHandler()


@pytest.fixture(scope="function", autouse=True)
def clear_data_handler(data_handler):
    """每个测试函数执行前清空全局变量"""
    data_handler.clear_global_vars()
    yield
