#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
文件用途：统一日志配置（文件详细 + 控制台可控）
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from config.config import Config

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_CONFIGURED = False
_CONSOLE_HANDLER: Optional[logging.Handler] = None

FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _ensure_log_dirs() -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)
    os.makedirs(os.path.join(_LOG_DIR, "daily"), exist_ok=True)
    os.makedirs(os.path.join(_LOG_DIR, "errors"), exist_ok=True)


def configure_logging(console_level: Optional[int] = None) -> None:
    """
    配置 root logger：文件 DEBUG，控制台级别可动态调整。

    CLI 模式建议 console_level=logging.WARNING，详细 IO 仅写入 logs/。
    """
    global _CONFIGURED, _CONSOLE_HANDLER

    if console_level is None:
        env_level = os.getenv("IFRIT_CONSOLE_LOG_LEVEL", "").upper()
        if env_level == "DEBUG":
            console_level = logging.DEBUG
        elif env_level == "WARNING":
            console_level = logging.WARNING
        elif env_level == "ERROR":
            console_level = logging.ERROR
        else:
            console_level = logging.INFO

    _ensure_log_dirs()
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    config = Config()
    if config.is_main_log_enabled():
        main_log = os.path.join(_LOG_DIR, "api_automation.log")
        main_handler = logging.FileHandler(main_log, encoding="utf-8")
        main_handler.setFormatter(FORMATTER)
        main_handler.setLevel(logging.DEBUG)
        root.addHandler(main_handler)

    if config.app_config.getboolean("logging", "daily_logs_enabled", fallback=True):
        today = datetime.now().strftime("%Y%m%d")
        daily_handler = logging.FileHandler(
            os.path.join(_LOG_DIR, "daily", f"daily_{today}.log"),
            encoding="utf-8",
        )
        daily_handler.setFormatter(FORMATTER)
        daily_handler.setLevel(logging.DEBUG)
        root.addHandler(daily_handler)

    if config.app_config.getboolean("logging", "error_daily_logs_enabled", fallback=True):
        today = datetime.now().strftime("%Y%m%d")
        error_handler = logging.FileHandler(
            os.path.join(_LOG_DIR, "errors", f"error_{today}.log"),
            encoding="utf-8",
        )
        error_handler.setFormatter(FORMATTER)
        error_handler.setLevel(logging.ERROR)
        root.addHandler(error_handler)

    _CONSOLE_HANDLER = logging.StreamHandler(sys.stdout)
    _CONSOLE_HANDLER.setFormatter(FORMATTER)
    _CONSOLE_HANDLER.setLevel(console_level)
    root.addHandler(_CONSOLE_HANDLER)

    _CONFIGURED = True


def set_console_level(level: int) -> None:
    """运行时调整控制台日志级别（不影响文件日志）。"""
    if _CONSOLE_HANDLER is not None:
        _CONSOLE_HANDLER.setLevel(level)


def get_logger(name: str = None) -> logging.Logger:
    """获取 logger（首次调用时完成 root 配置）。"""
    if not _CONFIGURED:
        configure_logging()
    if name is None:
        return logging.getLogger("ifrit")
    return logging.getLogger(name)


# 向后兼容
logger = get_logger("ifrit")
