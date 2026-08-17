#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
作者：孙文龙
文件用途：统一配置加载（.env + ini）
核心功能：dotenv 加载、ConfigParser 读取、环境变量覆盖
创建时间：2026-06-02
"""
import configparser
import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(BASE_DIR, "config", "settings")
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

_DOTENV_LOADED = False


def get_project_root() -> str:
    """返回项目根目录。"""
    return BASE_DIR


def load_dotenv(env_path: Optional[str] = None, override: bool = False) -> None:
    """
    加载 .env 到 os.environ（不引入第三方依赖）。

    Args:
        env_path: .env 文件路径，默认项目根目录
        override: 是否覆盖已存在的环境变量
    """
    global _DOTENV_LOADED
    path = env_path or ENV_FILE_PATH
    if not os.path.isfile(path):
        _DOTENV_LOADED = True
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key and (override or key not in os.environ):
                os.environ[key] = value

    _DOTENV_LOADED = True


def ensure_dotenv_loaded() -> None:
    """确保 .env 已加载（幂等）。"""
    if not _DOTENV_LOADED:
        load_dotenv()


def reload_dotenv(env_path: Optional[str] = None) -> None:
    """强制从 .env 文件重新加载（覆盖已有环境变量，供 UI 设置页使用）。"""
    global _DOTENV_LOADED
    _DOTENV_LOADED = False
    load_dotenv(env_path, override=True)
    _DOTENV_LOADED = True


def load_ini(filename: str) -> configparser.ConfigParser:
    """加载 config/settings/ 下的 ini 文件。"""
    ensure_dotenv_loaded()
    parser = configparser.ConfigParser()
    ini_path = os.path.join(SETTINGS_DIR, filename)
    if os.path.isfile(ini_path):
        parser.read(ini_path, encoding="utf-8")
    return parser


def get_env_value(key: str, default: str = "") -> str:
    """读取环境变量（自动加载 .env）。"""
    ensure_dotenv_loaded()
    return os.getenv(key, default).strip()


def get_env_override(key: str, ini_value: str) -> str:
    """环境变量非空时覆盖 ini 配置值。"""
    env_value = get_env_value(key)
    return env_value if env_value else ini_value


def get_dingtalk_config() -> dict:
    """读取钉钉机器人配置（仅来自 .env）。"""
    access_token = get_env_value("DINGTALK_ACCESS_TOKEN")
    keyword = get_env_value("DINGTALK_KEYWORD") or "通知"
    if not access_token:
        raise ValueError(
            "未设置 DINGTALK_ACCESS_TOKEN，请在 .env 中配置（参考 .env.example）"
        )
    webhook_url = (
        f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"
    )
    return {"webhook_url": webhook_url, "keyword": keyword}
