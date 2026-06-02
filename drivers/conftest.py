#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/9/10 上午10:07
# @Author  : sunwl
import logging
import os
import pytest

from core.request_handler import RequestHandler
from core.data_handler import DataHandler

os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

ENV_NAMES = []
AUTH_MANAGER = None

pytest_plugins = ["drivers.pytest_cli_plugin"]


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--env",
        action="append",
        help="指定运行环境，可以多次使用以指定多个环境，如 --env dev --env prod",
    )
    parser.addoption(
        "--test-data-file",
        action="store",
        default="",
        help="指定单个测试数据文件（csv/xlsx/json），仅加载该文件用例",
    )
    parser.addoption(
        "--suite",
        action="store",
        default="manual",
        choices=["manual", "ai", "smoke", "all"],
        help="用例套件：manual（人工）/ ai（AI生成）/ smoke（冒烟）/ all（全部目录）",
    )
    parser.addoption(
        "--global-auth",
        action="store_true",
        default=False,
        help="启用全局鉴权（session 登录，与用例内 login 步骤解耦）",
    )


def pytest_configure(config):
    """配置pytest"""
    global ENV_NAMES
    ENV_NAMES = config.getoption("--env") or []
    logging.info("Pytest configured with envs: %s", ENV_NAMES)


def pytest_sessionstart(session):
    """写入 Allure 环境信息。"""
    allure_dir = session.config.getoption("--alluredir")
    if not allure_dir:
        return
    from core.allure_env import write_allure_environment

    write_allure_environment(
        allure_dir=allure_dir,
        env_names=session.config.getoption("--env") or None,
        suite=session.config.getoption("--suite"),
        test_path=session.config.getoption("--test-data-file") or None,
    )


@pytest.fixture(scope="session")
def request_handler():
    """请求处理器 fixture"""
    from config.config import Config

    logging.info("Creating request handler with envs: %s", ENV_NAMES)
    config = Config(env_names=ENV_NAMES)
    base_url = config.get_base_url()
    timeout = config.get_timeout()
    logging.info("Request handler base_url: %s, timeout: %s", base_url, timeout)
    return RequestHandler(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="session")
def data_handler():
    """数据处理器 fixture"""
    return DataHandler()


@pytest.fixture(scope="session", autouse=True)
def global_auth(request_handler, data_handler, pytestconfig):
    """Session 级全局鉴权。"""
    global AUTH_MANAGER
    from core.auth_manager import AuthManager

    use_global = pytestconfig.getoption("--global-auth")
    AUTH_MANAGER = AuthManager(request_handler, data_handler, env_names=ENV_NAMES)
    if use_global or AUTH_MANAGER.auto_login:
        AUTH_MANAGER.ensure_logged_in()
    return AUTH_MANAGER


@pytest.fixture(scope="function")
def auth_manager():
    """供 TestExecutor 注入鉴权。"""
    return AUTH_MANAGER


@pytest.fixture(scope="function", autouse=True)
def preserve_auth_vars(data_handler):
    """每个用例前清空变量，但保留 token/username。"""
    protected = {}
    for key in ("token", "username", "address_id"):
        value = data_handler.get_variable(key)
        if value:
            protected[key] = value
    data_handler.clear_global_vars()
    for key, value in protected.items():
        data_handler.set_variable(key, value)
    yield
